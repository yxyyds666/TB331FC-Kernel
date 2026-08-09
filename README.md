# TB331FC-Kernel

小新Pad 2024 (TB331FC) 定制内核 —— **ReKernel** 系列

基于谷歌原版 **GKI 5.15.167** 编译,集成 **原版 KernelSU** + **SusFS 2.2.0**,带针对性性能优化。GitHub Actions 全自动云编译,构建完成后自动发布 Release。

## ✨ 特性

- **内核**:谷歌官方 GKI `android13-5.15.167_r00`(与设备 stock KMI 完全一致,vendor 模块兼容)
- **KernelSU (原版, 325xx+)**:内核级 root,兼容官方 Manager 32525
- **SusFS 2.2.0**:root 隐藏内核补丁(挂载伪装、路径隐藏、uname 伪装、打开重定向等)
- **性能优化**:关闭 KASAN(20-50% 性能损失)/ UBSAN / SLUB_DEBUG,`HZ=1000` 调度更跟手,`NR_CPUS=8` 精简 percpu,**-O3 全局编译**,**PELT half-life 16ms**(省电 ~5%),zram 换 **zstd** 压缩
- **全自动发布**:push 即构建,成功即生成 Release(v1.0.0 起,语义化版本号)

## 📦 产物

每次 Release 包含:

| 文件 | 说明 | 刷入方式 |
|---|---|---|
| `TB331FC-AnyKernel3.zip` (~23MB) | AK3 刷机包 | 设备端 TWRP/Manager 直接刷入,无需电脑 |
| `boot.img` (~43MB) | boot 分区镜像 | `fastboot flash boot boot.img` |
| `Image` | 裸内核 | 供二次开发 |

## 🔧 刷机

> 前提:bootloader 已解锁。

**方式 A:AnyKernel3 zip(推荐)**

1. 下载最新 Release 的 `TB331FC-AnyKernel3.zip`
2. KernelSU Manager → 刷入 → 选择 zip;或 TWRP/OrangeFox 刷入
3. 重启完成

**方式 B:fastboot**

```bash
adb reboot bootloader
fastboot flash boot boot.img
fastboot reboot
```

**方式 C:临时引导测试(不写入, 重启自动还原)**

```bash
adb reboot bootloader
fastboot boot boot.img
```

**回滚**:刷回原版 boot 分区镜像(`boot_a.img` 已存档于仓库)即可。

## 📋 版本号规范

版本号采用 `x.x.x` 三段式:

| 位 | 含义 | 触发方式 |
|---|---|---|
| 第一位 `x` | **重大更新**(内核大版本、root 架构变化等) | 手动触发 `workflow_dispatch` 选 `major` |
| 第二位 `x` | **补丁**(新增功能特性) | 手动触发 `workflow_dispatch` 选 `minor` |
| 第三位 `x` | **修补**(修复、小调整) | push 自动 `patch`(默认) |

首次发布固定 `v1.0.0`,之后自动递增。

## 🔄 开发流程

```bash
# 1. 修改代码/配置
# 2. 提交并推送 → 自动构建 + 自动发布 Release
git add . && git commit -m "..." && git push origin main

# 3. 需要升第二位/第一位版本时, 手动触发构建并选择 bump 方式:
gh workflow run build.yml -f bump=minor   # 或 major

# 4. 查看构建与发布状态
gh run list --repo yxyyds666/TB331FC-Kernel
gh release list --repo yxyyds666/TB331FC-Kernel
```

## ⚙️ 编译管线

```
GKI android13-5.15.167_r00
→ 原版 KernelSU (main) + SusFS 10_enable 补丁
→ SusFS 2.2.0 内核补丁 (50_add)
→ config.gz + 性能优化 (关 KASAN/UBSAN/SLUB_DEBUG, HZ=1000, NR_CPUS=8)
→ clang 17 编译 (ccache 加速)
→ repack boot.img + AK3 zip
→ 自动 Release
```

## 🛠 刷机后调优 (运行时)

```bash
adb push scripts/tune.sh /data/local/tmp/
adb shell su -c "sh /data/local/tmp/tune.sh"
```

调度延迟收紧 + swappiness=100(配合 zram)+ page-cluster=8,重启失效,可做成 KernelSU 模块持久化。

## 🌿 分支架构 (三分支)

| 分支 | 定位 | 内容 | Release |
|---|---|---|---|
| **main** | 正式内核 | **原汁原味** KernelSU + SusFS(无性能优化) | `vX.Y.Z` |
| **debug** | 调试内核 | main + 内核日志(pstore/宽容/动态调试) | `debug-vX.Y.Z` |
| **feature** | 实验内核 | main + 实验性优化补丁(O3/PELT/zstd, 不稳定) | `feature-vX.Y.Z` |

**main(正式)** — 原汁原味:KernelSU + SusFS 2.2.0,仅构建必需修复(thin LTO、whitelist 清理),**无任何性能优化**。

**debug(调试)** — main + 调试日志:

| 项 | main | debug |
|---|---|---|
| 内核日志 | 默认 | pstore/ramoops + 512KB 缓冲 + 全量动态调试 |
| 崩溃行为 | oops 即重启 | **oops 不重启**(保留现场抓日志) |
| SELinux | enforcing | **写死 permissive**(`androidboot.selinux=permissive enforcing=0`) |
| `dmesg` 权限 | root | 普通用户可读 |
| 产物 | `boot.img` | `boot-debug.img` + `TB331FC-debug-AnyKernel3.zip` |

**feature(实验)** — main + 实验优化,可能不稳定,仅建议 `fastboot boot` 临时引导测试:

| 实验项 | 内容 |
|---|---|
| 编译 | `-O3` 全局 + thin LTO |
| 调度 | PELT half-life 16ms、HZ=1000 |
| 其他 | zram zstd、NR_CPUS=8、关 KASAN/UBSAN/SLUB_DEBUG |

**拉取启动日志**(刷入 debug 内核、重启后):

```bash
adb shell cat /sys/fs/pstore/console-ramoops-0   # 启动/崩溃内核日志
adb shell dmesg | grep -iE "error|fail|panic"     # 当前日志
adb shell cat /sys/kernel/debug/dynamic_debug/control  # 动态调试开关
```

> 调试完建议刷回正式内核(宽容模式关闭 Android 安全隔离)。

## ⚠️ 说明

- **KPM 不含**:原版 KernelSU v3 已移除 KernelPatch/KPM 机制;如需 KPM 请改用 SukiSU-Ultra 构建
- SusFS 为实验性代码,可能存在性能损耗或稳定性问题
- 内核仅供学习研究使用,刷机风险自负

## 🔗 相关项目

- [KernelSU](https://github.com/tiann/KernelSU) / [SukiSU-Ultra](https://github.com/SukiSU-Ultra/SukiSU-Ultra)
- [SusFS (simonpunk)](https://gitlab.com/simonpunk/susfs4ksu)
- [AnyKernel3 (WildKernels)](https://github.com/WildKernels/AnyKernel3)
