#!/vendor/bin/sh
# Autonomous 90-Second Boot Watchdog for SM-M326B
TIMEOUT=600
ELAPSED=0

echo "[boot_watchdog] Autonomous 90s Boot Watchdog armed." > /dev/kmsg

while [ $ELAPSED -lt $TIMEOUT ]; do
    BOOTED=$(getprop sys.boot_completed)
    if [ "$BOOTED" = "1" ]; then
        echo "[boot_watchdog] Branch A: sys.boot_completed=1 confirmed. Watchdog disarmed." > /dev/kmsg
        exit 0
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

BOOTED=$(getprop sys.boot_completed)
if [ "$BOOTED" = "1" ]; then
    echo "[boot_watchdog] Branch A: sys.boot_completed=1 confirmed at deadline. Disarmed." > /dev/kmsg
    exit 0
fi

echo "[boot_watchdog] Branch B: System hang detected after 90s! Auto-rebooting to TWRP Recovery..." > /dev/kmsg
# Auto-Recovery BCB write
echo -n -e "boot-recovery\0" > /dev/block/by-name/misc
sync
setprop sys.powerctl reboot,recovery
/system/bin/reboot recovery 2>/dev/null
/vendor/bin/reboot recovery 2>/dev/null
sleep 5
echo b > /proc/sysrq-trigger
