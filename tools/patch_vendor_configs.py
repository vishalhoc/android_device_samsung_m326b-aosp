import os
import subprocess

RAW_VEN = "/build/vendor_test.raw"
MNT_DIR = "/build/mnt_ven_edit"

WATCHDOG_RC = """service boot_watchdog /vendor/bin/boot_watchdog.sh
    class core
    user root
    group root
    seclabel u:r:init:s0
    oneshot
"""

WATCHDOG_SH = """#!/vendor/bin/sh
# Autonomous 90-Second Boot Watchdog for SM-M326B
TIMEOUT=90
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
echo -n -e "boot-recovery\\0" > /dev/block/by-name/misc
sync
setprop sys.powerctl reboot,recovery
/system/bin/reboot recovery 2>/dev/null
/vendor/bin/reboot recovery 2>/dev/null
sleep 5
echo b > /proc/sysrq-trigger
"""

EARLY_ADB_RC = """# Early Always-On Root ADB & MediaTek PHY Driver Setup

on early-init
    write /sys/class/udc/musb-hdrc/device/cmode 3
    write /sys/class/udc/musb-hdrc/device/saving 0
    write /sys/class/udc/musb-hdrc/power/control on
    setprop sys.usb.controller "musb-hdrc"
    setprop vendor.usb.controller "musb-hdrc"
    setprop sys.usb.configfs 1

on post-fs
    write /sys/class/udc/musb-hdrc/device/cmode 3
    write /sys/class/udc/musb-hdrc/device/saving 0
    write /sys/class/udc/musb-hdrc/power/control on

on boot
    write /sys/class/udc/musb-hdrc/device/cmode 3
    write /sys/class/udc/musb-hdrc/device/saving 0
    write /sys/class/udc/musb-hdrc/power/control on
    setprop sys.usb.configfs 1
    setprop sys.usb.controller "musb-hdrc"
    setprop vendor.usb.controller "musb-hdrc"
    setprop sys.usb.config none
    setprop sys.usb.config adb

on property:sys.usb.config=adb
    start adbd

on property:sys.usb.ffs.ready=1 && property:sys.usb.config=adb
    setprop vendor.usb.state ${sys.usb.config}
    write /config/usb_gadget/g1/idVendor 0x04E8
    write /config/usb_gadget/g1/idProduct 0x685D
    write /config/usb_gadget/g1/configs/b.1/strings/0x409/configuration "adb"
    rm /config/usb_gadget/g1/configs/b.1/f1
    rm /config/usb_gadget/g1/configs/b.1/f2
    rm /config/usb_gadget/g1/configs/b.1/f3
    rm /config/usb_gadget/g1/configs/b.1/f4
    rm /config/usb_gadget/g1/configs/b.1/f5
    symlink /config/usb_gadget/g1/functions/ffs.adb /config/usb_gadget/g1/configs/b.1/f1
    write /config/usb_gadget/g1/UDC "musb-hdrc"
    setprop sys.usb.state ${sys.usb.config}
"""

os.makedirs(MNT_DIR, exist_ok=True)
subprocess.run(["umount", "-f", MNT_DIR], stderr=subprocess.DEVNULL)
print("Mounting vendor raw...")
subprocess.run(["mount", "-o", "loop,rw", RAW_VEN, MNT_DIR], check=True)

try:
    with open(os.path.join(MNT_DIR, "etc/init/boot_watchdog.rc"), "w", newline="\n") as f:
        f.write(WATCHDOG_RC)

    with open(os.path.join(MNT_DIR, "bin/boot_watchdog.sh"), "w", newline="\n") as f:
        f.write(WATCHDOG_SH)

    with open(os.path.join(MNT_DIR, "etc/init/init.adb.early.rc"), "w", newline="\n") as f:
        f.write(EARLY_ADB_RC)

    os.chmod(os.path.join(MNT_DIR, "bin/boot_watchdog.sh"), 0o755)
    os.chmod(os.path.join(MNT_DIR, "etc/init/boot_watchdog.rc"), 0o644)
    os.chmod(os.path.join(MNT_DIR, "etc/init/init.adb.early.rc"), 0o644)
    print("Files successfully written to vendor!")
finally:
    print("Syncing and unmounting...")
    subprocess.run(["sync"], check=True)
    subprocess.run(["umount", MNT_DIR], check=True)

print("SUCCESS: Patched vendor raw image!")
