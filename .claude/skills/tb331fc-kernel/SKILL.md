---
name: tb331fc-kernel
description: TB331FC (小新Pad 2024) 内核云编译全流程 — 构建、发布、刷机、版本管理。用于"编译内核/发新版/更新内核/刷机"等请求。
---

# TB331FC Kernel 工作流

小新Pad 2024 (TB331FC) 定制内核:谷歌原版 GKI 5.15.167 + ReSukiSU (KernelSU) + SusFS,GitHub Actions 云编译 + 自动 Release。

## 仓库结构

- `config.gz` — 设备原版内核配置 (5.15.167)
- `boot_a.img` — 原版 boot 分区 (header v4, 无 ramdisk, 回滚用)
- `.github/workflows/build.yml` — 云编译 + 自动发布管线
- `scripts/repack.py` — boot.img 重打包 (替换内核段, 可选融合 vendor ramdisk)
- `scripts/bump_version.sh` — 版本递增 (patch/minor/major)
- `scripts/tune.sh` — 刷机后运行时调优

## 编译管线 (build.yml)

```
GKI android13-5.15.167_r00 (google common 仓库)
→ ReSukiSU (内置 SusFS 适配, 多管理器, KSU_VERSION 349xx)
→ SusFS 2.2.0 内核补丁 (50_add_susfs_in_gki-android13-5.15.patch + fs/susfs.c + include/linux/*)
→ config.gz + 性能优化 (关 KASAN/UBSAN/SLUB_DEBUG, HZ=1000, NR_CPUS=8)
→ clang 17 + ccache 编译 → repack boot.img + AK3 zip
→ 自动创建 GitHub Release
```

## 标准操作流程

### 1. 发布新版本 (push 即触发)

```bash
git add . && git commit -m "<改动说明>" && git push origin main
```

- push 后自动构建,成功后自动 Release,**版本号自动 patch+1**(第三位)
- 升第二位(补丁/新功能)或第一位(重大更新)时:

```bash
gh workflow run build.yml -f bump=minor   # 第二位 +1
gh workflow run build.yml -f bump=major   # 第一位 +1
```

### 2. 查看状态

```bash
gh run list --repo yxyyds666/TB331FC-Kernel --limit 3
gh release list --repo yxyyds666/TB331FC-Kernel --limit 3
gh run view <run_id> --repo yxyyds666/TB331FC-Kernel --log-failed   # 失败日志
```

### 3. 下载产物

```bash
gh release download --repo yxyyds666/TB331FC-Kernel --pattern "TB331FC-AnyKernel3.zip"   # 或 boot.img
```

### 4. 刷机

```bash
adb reboot bootloader
fastboot boot boot.img        # 先临时引导测试 (不写入, 重启还原)
# 正常后:
fastboot flash boot boot.img  # 持久化
```

或设备端直接刷 `TB331FC-AnyKernel3.zip` (TWRP/KernelSU Manager)。

### 5. 回滚

```bash
fastboot flash boot boot_a.img   # 仓库内原版镜像
```

## 修改内核配置时注意

1. **config 变更会让 ccache 几乎全失效**(autoconf.h 依赖),构建时间回到全量
2. KMI 约束:保持 `android13-5.15.167` 版本与 stock 一致,否则 vendor 模块可能不加载
3. `CONFIG_KSU_SUSFS` 同时控制内核侧 `fs/susfs.o` 编译,无独立 CONFIG_SUSFS
4. **KPM 不在本内核**:ReSukiSU 已移除 KernelPatch;需要 KPM 换 SukiSU-Ultra
5. `PREEMPT_DYNAMIC` 是 6.x 特性,5.15 无此符号
6. vendor config 含构建机绝对路径依赖 (`abi_symbollist.raw`),必须 `--undefine UNUSED_KSYMS_WHITELIST` + `--undefine TRIM_UNUSED_KSYMS`

## 常见故障排查

| 症状 | 处理 |
|---|---|
| SusFS 补丁 hunk 失败 | SusFS 分支与 KernelSU 版本漂移;换分支或固定 commit |
| `susfs_def.h not found` | include 目录必须整目录复制 (`cp -r .../include/linux/.`) |
| 编译 OOM | Full LTO 改 thin LTO (workflow 已内置) |
| Manager 版本不匹配 | 内核 KSU_VERSION ≥ Manager 要求;ReSukiSU 349xx 兼容官方 Manager 32525 |
