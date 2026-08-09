# TB331FC-Kernel

小新Pad 2024 (TB331FC) 定制内核 —— **ReKernel** 系列

基于谷歌原版 **GKI 5.15.167** 编译,集成**原版 KernelSU** + **SusFS 2.2.0**。GitHub Actions 矩阵云编译,每次发布**单个 Release 含三个变体**(main / debug / feature)。

## ✨ 特性

- **内核**:谷歌官方 GKI `android13-5.15.167_r00`(与设备 stock KMI 完全一致,vendor 模块兼容)
- **原版 KernelSU**(325xx+,兼容官方 Manager):内核级 root
- **SusFS 2.2.0**:root 隐藏内核补丁(挂载伪装、路径隐藏、uname 伪装、打开重定向等)
- **三变体单 Release**:一次发布同时提供 正式 / 调试 / 实验 三种内核,按需选择

## 📦 产物 (每个 Release 六个文件)

| 文件 | 变体 | 说明 |
|---|---|---|
| `boot-main.img` / `TB331FC-main-AnyKernel3.zip` | main | **原汁原味**:KernelSU + SusFS,无性能优化,日常使用 |
| `boot-debug.img` / `TB331FC-debug-AnyKernel3.zip` | debug | main + 调试日志(pstore 保留、512KB 缓冲、动态调试、oops 不重启、SELinux 写死宽容),问题定位用 |
| `boot-feature.img` / `TB331FC-feature-AnyKernel3.zip` | feature | main + **实验性优化**(-O3 编译、PELT 16ms、zram zstd、HZ=1000、关 KASAN),不稳定,仅供测试 |

> 三个变体共用同一 GKI 5.15.167 内核与 KMI,可互相替换刷入。

## 🔧 刷机

> 前提:bootloader 已解锁。按需选择变体(下文以 main 为例)。

**方式 A:AK3 zip(设备端,推荐)**

1. 下载最新 Release 的 `TB331FC-main-AnyKernel3.zip`
2. KernelSU Manager → 刷入 → 选择 zip;或 TWRP/OrangeFox 刷入
3. 重启完成

**方式 B:fastboot**

```bash
adb reboot bootloader
fastboot flash boot boot-main.img
fastboot reboot
```

**方式 C:临时引导测试(不写入, 重启自动还原)**

```bash
fastboot boot boot-main.img
```

**回滚**:刷回原版 boot 分区镜像(`boot_a.img` 已存档于仓库)即可。

## 🌿 变体架构

三个变体由**矩阵构建**并行产出,汇总为单个 Release(不在 debug/feature 分支单独发版):

| 变体 | 定位 | 与 main 的差异 |
|---|---|---|
| **main** | 正式 | —(原汁原味, 无性能优化) |
| **debug** | 调试 | `PANIC_ON_OOPS` 关闭(oops 不重启保留现场)、`LOG_BUF_SHIFT` 17→19(512KB 日志)、`DYNAMIC_DEBUG` 全量、cmdline 写死宽容 `androidboot.selinux=permissive enforcing=0` |
| **feature** | 实验 | 关 `KASAN`/`UBSAN`/`SLUB_DEBUG`、`HZ=1000`、`NR_CPUS=8`、zram zstd、PELT half-life 16ms、`-O3` 全局编译 |

> 注:参数调整属于 feature 变体的实验内容,main 不包含。

## 📋 版本号规范

版本号采用 `x.x.x` 三段式:

| 位 | 含义 | 触发方式 |
|---|---|---|
| 第一位 `x` | **重大更新**(内核大版本、root 架构变化等) | 手动触发 `workflow_dispatch` 选 `major` |
| 第二位 `x` | **补丁**(新增功能特性) | 手动触发 `workflow_dispatch` 选 `minor` |
| 第三位 `x` | **修补**(修复、小调整) | push 自动 `patch`(默认) |

## 🔄 开发流程

```bash
# 1. 修改代码/配置
# 2. 提交并推送 → 自动矩阵构建 + 自动发布 Release (三变体六文件)
git add . && git commit -m "..." && git push origin main

# 3. 需要升第二位/第一位版本时, 手动触发:
gh workflow run build.yml -f bump=minor   # 或 major

# 4. 查看构建与发布状态
gh run list --repo yxyyds666/TB331FC-Kernel
gh release list --repo yxyyds666/TB331FC-Kernel
```

## ⚙️ 编译管线 (每个变体)

```
GKI android13-5.15.167_r00
→ 原版 KernelSU (main) + SusFS (10_enable + 50_add 补丁)
→ [feature] PELT 16ms 补丁
→ config.gz + 构建修复 + [feature] 性能项 + [debug] 调试项
→ clang 17 编译 (ccache 加速) → repack boot-<变体>.img + AK3 zip
→ publish: 六文件合并发布单个 Release
```

## 🛠 刷机后调优 (运行时, 可选)

```bash
adb push scripts/tune.sh /data/local/tmp/
adb shell su -c "sh /data/local/tmp/tune.sh"
```

调度延迟收紧 + swappiness=100(配合 zram)+ page-cluster=8,重启失效,可做成 KernelSU 模块持久化。

## ⚠️ 说明

- **KPM 不含**:原版 KernelSU v3 已移除 KernelPatch/KPM 机制;如需 KPM 请改用 SukiSU-Ultra 构建
- SusFS 为实验性代码,可能存在性能损耗或稳定性问题;feature 变体未经长期稳定性验证
- 内核仅供学习研究使用,刷机风险自负

## 🔗 相关项目

- [KernelSU](https://github.com/tiann/KernelSU) / [SukiSU-Ultra](https://github.com/SukiSU-Ultra/SukiSU-Ultra)
- [SusFS (simonpunk)](https://gitlab.com/simonpunk/susfs4ksu)
- [AnyKernel3 (WildKernels)](https://github.com/WildKernels/AnyKernel3)
