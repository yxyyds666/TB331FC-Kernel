# TB331FC-Kernel

小新Pad 2024 (TB331FC) 内核编译仓库 —— 谷歌原版 **GKI 5.15.167** + **KernelSU**,由 GitHub Actions 云端编译打包。

## 仓库文件

| 文件 | 说明 |
|---|---|
| `config.gz` | 设备原版内核配置 (Linux/arm64 5.15.167, 来自 `/proc/config.gz`) |
| `boot_a.img` | 设备原版 boot 分区镜像 (header v4, 无 ramdisk, raw Image) |
| `scripts/repack.py` | boot.img 重打包脚本 (替换内核段, 保留原 header) |
| `.github/workflows/build.yml` | 云编译工作流 |

## 编译流程 (push 自动触发)

1. 拉取谷歌官方 GKI 源码 `android13-5.15.167_r00` (与设备内核版本一致, KMI 兼容)
2. 集成 KernelSU `v3.2.5` (KSU_VERSION≈32513, 兼容最新 Manager 32525)
3. 集成 SusFS `gki-android13-5.15` 分支 (root 隐藏补丁, 与 KernelSU main 同步维护)
4. 应用设备配置 `config.gz` + 性能优化 (关闭厂商工程调试项, 见下)
5. `make LLVM=1` (clang 17) 编译 → `scripts/repack.py` 重打包 `boot.img` 上传 artifact

## 性能优化项

基于厂商工程配置 (config.gz) 的针对性优化:

| 优化 | 说明 |
|---|---|
| 关闭 `CONFIG_KASAN` | 内存错误检测器, 20-50% 性能损失, 量产必须关 |
| 关闭 `CONFIG_UBSAN` | 未定义行为检测, 运行时开销 |
| 关闭 `CONFIG_SLUB_DEBUG` | slub 调试, 内存/性能开销 |
| `HZ` 250 → 1000 | 调度 tick 更密, 交互/游戏更跟手 |
| Full LTO → thin LTO | 官方 GKI 同款, 避免 CI 内存不足 |
| 清除 whitelist/trim-ksyms | 移除厂商构建机绝对路径依赖 |

## 说明

- KPM (Kernel Patch Module) 在原版 KernelSU v3.x 中已移除 (仅 SukiSU 等 fork 保留); SusFS 的隐藏模块走普通 KSU 模块方式, 不依赖 KPM。

## 刷机

1. 在仓库 Actions 页面下载最新 artifact 中的 `boot.img`
2. 连接设备, 执行:

```bash
adb reboot bootloader
fastboot flash boot boot.img
fastboot reboot
```

> 要求 bootloader 已解锁。

## 回滚

原版镜像已在仓库内 (`boot_a.img`), 直接刷回即可:

```bash
fastboot flash boot boot_a.img
```

## 验证 KernelSU

```bash
# 1. 确认内核配置 (KALLSYMS 为 KernelSU 必需项)
adb shell zcat /proc/config.gz | grep KALLSYMS
# 2. 安装 KernelSU Manager (https://github.com/tiann/KernelSU/releases) 并授权
adb shell su -c id   # 应输出 uid=0
```
