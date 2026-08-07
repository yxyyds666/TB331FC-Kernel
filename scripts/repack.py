#!/usr/bin/env python3
"""
TB331FC boot.img 重打包脚本

从原版 boot_a.img(header v4, 无 ramdisk)复制头部并更新 kernel_size,
将内核段替换为新编译的 Image,输出可 fastboot 刷写的 boot.img。

用法:
    python3 repack.py --input boot_a.img --kernel arch/arm64/boot/Image --output boot.img
"""
import argparse
import struct
from pathlib import Path

PAGE_SIZE = 4096


def main() -> None:
    ap = argparse.ArgumentParser(description="重打包 GKI boot.img (header v4)")
    ap.add_argument("--input", required=True, help="原版 boot 镜像 (如 boot_a.img)")
    ap.add_argument("--kernel", required=True, help="新编译的内核 Image")
    ap.add_argument("--output", required=True, help="输出 boot.img")
    args = ap.parse_args()

    orig = Path(args.input).read_bytes()
    kernel = Path(args.kernel).read_bytes()

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
    out = bytearray(PAGE_SIZE)
    out[:header_size] = header
    out += kernel

    pad = (PAGE_SIZE - (len(out) % PAGE_SIZE)) % PAGE_SIZE
    out += b"\x00" * pad

    Path(args.output).write_bytes(out)
    print(f"[+] 已生成 {args.output} ({len(out)}B)")
    print(f"[+] kernel_size 已更新: {len(kernel)}B")


if __name__ == "__main__":
    main()
