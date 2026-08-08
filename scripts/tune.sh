#!/system/bin/sh
# TB331FC 刷机后调度/内存调优脚本 (Plan A)
# 用法: adb push 到 /data/local/tmp 后 adb shell su -c "sh /data/local/tmp/tune.sh"
# 说明: 均为运行时参数, 重启失效; 如需持久化请做成 KernelSU 模块 (service.sh 中执行)

echo "[*] 调度参数收紧 (默认 6ms/2.25ms/1.5ms -> 4ms/1ms/0.8ms)"
echo 4000000 > /proc/sys/kernel/sched_latency_ns
echo 1000000 > /proc/sys/kernel/sched_min_granularity_ns
echo 800000  > /proc/sys/kernel/sched_wakeup_granularity_ns

echo "[*] 内存参数 (配合 zram 启用)"
echo 100 > /proc/sys/vm/swappiness
echo 8   > /proc/sys/vm/page-cluster

echo "[*] 完成:"
cat /proc/sys/kernel/sched_latency_ns /proc/sys/kernel/sched_min_granularity_ns \
    /proc/sys/kernel/sched_wakeup_granularity_ns /proc/sys/vm/swappiness \
    /proc/sys/vm/page-cluster
