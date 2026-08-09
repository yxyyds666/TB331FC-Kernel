---
name: tb331fc-kernel
description: TB331FC (小新Pad 2024) 内核云编译全流程 — 矩阵构建、单 Release 三产物、刷机、版本管理。用于"编译内核/发新版/更新内核/刷机/发布"等请求。
---

# TB331FC Kernel 工作流

小新Pad 2024 (TB331FC) 定制内核:谷歌原版 GKI 5.15.167 + **原版 KernelSU** + SusFS 2.2.0,GitHub Actions 矩阵云编译,**每次 Release 打包 3 个变体**。

## 仓库结构

- `config.gz` — 设备原版内核配置 (5.15.167, 来自 /proc/config.gz)
- `boot_a.img` — 原版 boot 分区 (header v4, 无 ramdisk, 回滚用)
- `.github/workflows/build.yml` — 矩阵构建 + 汇总发布管线
- `scripts/repack.py` — boot.img 重打包 (替换内核段, 支持 --cmdline 注入 / --vendor-ramdisk)
- `scripts/bump_version.sh` — 版本递增 (patch/minor/major)
- `scripts/tune.sh` — 刷机后运行时调优
- `scripts/patch/pelt-half-life-16ms.patch` — PELT 16ms 补丁 (feature 变体用)

## 三变体架构 (矩阵构建)

workflow 用 `strategy.matrix.variant: [main, debug, feature]` 并行构建,三个 job 独立产出,`publish` job 汇总为**单个 Release**:

| 变体 | 定位 | 差异 | 产物 |
|---|---|---|---|
| **main** | 正式 | 原汁原味 KSU + SusFS, 无性能优化 | `boot-main.img` + `TB331FC-main-AnyKernel3.zip` |
| **debug** | 调试 | main + pstore/512KB 日志/动态调试/oops 不重启 | `boot-debug.img` + `TB331FC-debug-AnyKernel3.zip` |
| **feature** | 实验 | main + O3/PELT 16ms/zstd/HZ=1000/NR_CPUS=8/关 KASAN (不稳定) | `boot-feature.img` + `TB331FC-feature-AnyKernel3.zip` |

分支仅作源码管理(debug/feature 分支存在),**构建内容由矩阵 variant 决定**,与分支无关。

## 编译管线 (每个变体)

```
GKI android13-5.15.167_r00 (google common 仓库)
→ 原版 KernelSU main (tiann/KernelSU, setup.sh 集成)
→ SusFS: 10_enable (KSU 驱动侧) + 50_add (内核侧) + fs/susfs.c + include/linux/*
→ [feature only] PELT 16ms 补丁
→ config.gz + 构建修复 (whitelist/trim/LTO thin) + [feature] 性能项 + [debug] 调试项
→ clang 17 + ccache → Image → repack boot-<variant>.img + AK3 zip
→ publish: 六文件合并发布一个 Release
```

## 标准操作流程

### 1. 发布新版本

```bash
git add . && git commit -m "<说明>" && git push origin main   # 自动构建, 版本 patch+1
```

- push 到 main 触发全矩阵构建(3 变体并行, 约 30-50 分钟),成功后自动发布
- 升第二位(新功能)或第一位(重大更新):
  ```bash
  gh workflow run build.yml -f bump=minor   # 第二位 +1
  gh workflow run build.yml -f bump=major   # 第一位 +1
  ```
- **不想 push 触发构建**时:commit 消息加 `[skip ci]`,然后手动 dispatch

### 2. 查看状态

```bash
gh run list --repo yxyyds666/TB331FC-Kernel --limit 3
gh run view <run_id> --repo yxyyds666/TB331FC-Kernel --log-failed   # 失败日志
gh run view <run_id> --repo yxyyds666/TB331FC-Kernel --json jobs -q '.jobs[] | .name + " " + .status'  # 矩阵各 job
```

### 3. 下载产物

```bash
gh release download <tag> --repo yxyyds666/TB331FC-Kernel   # 一次拿全 6 文件
# 或浏览器 https://github.com/yxyyds666/TB331FC-Kernel/releases
```

### 4. 刷机

```bash
adb reboot bootloader
fastboot boot boot-main.img        # 先临时引导测试 (不写入, 重启还原)
# 正常后:
fastboot flash boot boot-main.img  # 持久化
# 或 AK3 zip 设备端刷入 (TWRP/KernelSU Manager)
```

### 5. 回滚

```bash
fastboot flash boot boot_a.img     # 仓库内原版镜像
```

### 6. 拉取启动日志 (debug 变体)

```bash
adb shell cat /sys/fs/pstore/console-ramoops-0   # 崩溃/启动日志
adb shell dmesg | grep -iE "error|fail|panic"    # debug 变体免 root
adb logcat -b crash -d                            # 应用崩溃
```

## 版本号规则

`x.x.x` = 重大更新.补丁.修补;首次发布固定 v1.0.0;push 自动 patch+1;dispatch 可选 minor/major。

## 修改内核配置时注意

1. **config 变更会让 ccache 几乎全失效**(autoconf.h 依赖),构建时间回到全量
2. KMI 约束:保持 `android13-5.15.167` 版本与 stock 一致,否则 vendor 模块可能不加载
3. `CONFIG_KSU_SUSFS` 由 SusFS 10_enable 补丁添加,同时控制内核侧 `fs/susfs.o` 编译,无独立 CONFIG_SUSFS
4. `PREEMPT_DYNAMIC` 是 6.x 特性,5.15 无此符号
5. vendor config 含构建机绝对路径依赖 (`abi_symbollist.raw`),必须 `--undefine UNUSED_KSYMS_WHITELIST` + `--undefine TRIM_UNUSED_KSYMS`
6. **KPM 不在本内核**:原版 KernelSU v3 已移除 KernelPatch;需要 KPM 换 SukiSU-Ultra
7. 所有变量修改走矩阵 variant 判断 (`$VARIANT`),不要按分支名判断

## 常见故障排查

| 症状 | 处理 |
|---|---|
| SusFS 补丁 hunk 失败 | SusFS 分支与 KernelSU 版本漂移;KernelSU 用 main (补丁同步), 或固定 SusFS commit |
| `susfs_def.h not found` | include 目录必须整目录复制 (`cp -r .../include/linux/. include/linux/`) |
| 编译 OOM | Full LTO 改 thin LTO (workflow 已内置) |
| Manager 版本不匹配 | 内核 KSU_VERSION ≥ Manager 要求;原版 main 325xx+ 兼容官方 Manager 32525 |
| 版本号前缀重复 (debug-debug-x) | bump_version.sh 剥离逻辑须兼容无 v 的 tag (已修复: `${LATEST#${PREFIX}}` + `${VER#v}`) |
| PELT 步骤 grep 失败 | 步骤 cwd 是 workspace 根, 路径写 `kernel/sched/sched-pelt.h` |
| bootloop 排查 | 先刷 boot-main.img (最干净);仍 bootloop 则二分: 无 SusFS 仅 KSU 隔离版 |
| Release 缺某变体 | publish job 检测三个 boot 文件齐全才发布, 缺失时查对应 build job 日志 |
| 矩阵产物同名覆盖 | 三变体上传同名文件 (Image/.config) 会互相覆盖; 必须改名 Image-<variant> 后再上传 |
| .config 上传无效 | upload-artifact v4 忽略隐藏文件; 需复制为 config-<variant> 非隐藏名 |
| ccache 互相驱逐 | GitHub 单仓库 cache 上限 10GB, 矩阵三变体各 2G (18G 会持续互驱) |
| publish 红叉 | 不需要 `if: always()`, needs 默认 build 全成功才运行 |

## 调试内核要点

- debug 变体: `oops 不重启` (PANIC_ON_OOPS 关) + 512KB 日志缓冲 + 全量动态调试
- **严禁注入 boot cmdline**: 原版 cmdline 为空, 高通 ABL 对非空 cmdline 处理缺陷导致无法开机 (实机验证); 宽容用运行时 `su -c setenforce 0`
- pstore 文件拉完即删 (`rm /sys/fs/pstore/*`), 否则下次崩溃日志混叠
- 崩溃现场: `su -c cat /sys/fs/pstore/console-ramoops-0` (需要 root, KSU 授权后可用)
