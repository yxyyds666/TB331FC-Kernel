#!/usr/bin/env python3
"""
TB331FC boot.img 重打包脚本

从原版 boot_a.img(header v4, 无 ramdisk)复制头部并更新 kernel_size,
将内核段替换为新编译的 Image,可选融合 vendor ramdisk,
输出可 fastboot 刷写/临时引导的 boot.img。

用法:
    python3 repack.py --input boot_a.img --kernel arch/arm64/boot/Image \
        [--vendor-ramdisk vendor_ramdisk.gz] --output boot.img
"""
import argparse
import struct
from pathlib import Path

PAGE_SIZE = 4096

# v4 header: vendor_ramdisk_size 位于 header 末尾 (boot_img_hdr_v4 在
# boot_img_hdr_v3 之后追加 4 字节), 其偏移 = header_size - 4
V4_VENDOR_RAMDISK_OFFSET = 1580


def align_page(n: int) -> int:
    return (n + PAGE_SIZE - 1) // PAGE_SIZE * PAGE_SIZE


def main() -> None:
    ap = argparse.ArgumentParser(description="重打包 GKI boot.img (header v4)")
    ap.add_argument("--input", required=True, help="原版 boot 镜像 (如 boot_a.img)")
    ap.add_argument("--kernel", required=True, help="新编译的内核 Image")
    ap.add_argument("--vendor-ramdisk", default=None,
                    help="vendor ramdisk (gzip cpio), 融合进 boot.img 供临时引导使用")
    ap.add_argument("--cmdline", default=None,
                    help="写入 boot header cmdline 字段 (如 androidboot.selinux=permissive enforcing=0)")
    ap.add_argument("--output", required=True, help="输出 boot.img")
    args = ap.parse_args()

    orig = Path(args.input).read_bytes()
    kernel = Path(args.kernel).read_bytes()
    vram = Path(args.vendor_ramdisk).read_bytes() if args.vendor_ramdisk else None

    if orig[:8] != b"ANDROID!":
        raise SystemExit(f"[ERROR] {args.input} 不是有效的 Android boot 镜像")

    kernel_size = struct.unpack_from("<I", orig, 8)[0]
    ramdisk_size = struct.unpack_from("<I", orig, 12)[0]
    header_size = struct.unpack_from("<I", orig, 20)[0]
    header_version = struct.unpack_from("<I", orig, 40)[0]

    print(f"[*] 原镜像: header v{header_version}, kernel={kernel_size}B, ramdisk={ramdisk_size}B")
    if header_version != 4:
        raise SystemExit(f"[ERROR] 仅支持 header v4, 实际为 v{header_version}")
    if ramdisk_size != 0:
        raise SystemExit("[ERROR] 原镜像含 ramdisk, 本脚本未处理该情况")
    print(f"[*] 新内核: {len(kernel)}B")

    # 复制原 header(保留 os_version 等字段), 更新 kernel_size, 补零到页对齐
    header = bytearray(orig[:header_size])
    struct.pack_into("<I", header, 8, len(kernel))
    # 可选: 写入 cmdline (v4: 位于 offset 44, 长 1536 字节, 原值为空)
    if args.cmdline:
        cmd_off = 44
        cmd_len = 1536
        data = args.cmdline.encode()
        if len(data) >= cmd_len:
            raise SystemExit(f"[ERROR] cmdline 过长 ({len(data)}B >= {cmd_len}B)")
        header[cmd_off:cmd_off + cmd_len] = b"\x00" * cmd_len
        header[cmd_off:cmd_off + len(data)] = data
        print(f"[+] 已写入 cmdline: {args.cmdline}")
    out = bytearray(PAGE_SIZE)
    out[:header_size] = header
    out += kernel
    out += b"\x00" * (align_page(len(out)) - len(out))  # kernel 段页对齐

    # 可选: 融合 vendor ramdisk (v4: 位于 kernel 之后, 头部记录大小)
    if vram:
        if len(out) + len(vram) > 96 * 1024 * 1024:  # boot 分区实际 96MiB (100663296B)
            raise SystemExit(f"[ERROR] 融合后镜像 ({len(out)+len(vram)}B) 超出 "
                             "boot 分区大小 (96MiB)")
        struct.pack_into("<I", header, V4_VENDOR_RAMDISK_OFFSET, len(vram))
        out[:header_size] = header
        out += vram
        out += b"\x00" * (align_page(len(out)) - len(out))
        print(f"[+] 已融合 vendor ramdisk: {len(vram)}B")
    else:
        print("[!] 未提供 vendor ramdisk, 仅包含内核")

    Path(args.output).write_bytes(out)
    print(f"[+] 已生成 {args.output} ({len(out)}B)")
    print(f"[+] kernel_size={len(kernel)}B, vendor_ramdisk_size="
          f"{struct.unpack_from('<I', header, V4_VENDOR_RAMDISK_OFFSET)[0]}B")


if __name__ == "__main__":
    main()
