import os
import shutil
import subprocess

RAW_VEN = "/build/vendor_test.raw"
MNT_DIR = "/build/mnt_ven_edit"
GENUINE_KM_BIN = "/build/lineage20/out/soong/.intermediates/hardware/interfaces/keymaster/4.0/default/android.hardware.keymaster@4.0-service/android_arm64_armv8-2a_cortex-a76_cfi/android.hardware.keymaster@4.0-service"

print("==========================================================")
print("  Applying Genuine AOSP Pure Software Keymaster 4.0 Fix")
print("==========================================================")

os.makedirs(MNT_DIR, exist_ok=True)
subprocess.run(["umount", "-f", MNT_DIR], stderr=subprocess.DEVNULL)
print("[1/5] Mounting vendor raw image...")
subprocess.run(["mount", "-o", "loop,rw", RAW_VEN, MNT_DIR], check=True)

try:
    # 1. Install genuine AOSP Keymaster 4.0 binary
    print("[2/5] Installing genuine AOSP software Keymaster 4.0 binary...")
    target_km = os.path.join(MNT_DIR, "bin/hw/android.hardware.keymaster@4.0-service")
    shutil.copy2(GENUINE_KM_BIN, target_km)
    os.chmod(target_km, 0o755)
    print(f"  -> Injected {target_km} ({os.path.getsize(target_km):,} bytes)")

    # 2. Remove Samsung proprietary skeymaster device
    print("[3/5] Removing Samsung TEEGRIS skeymaster library...")
    skeymaster_so = os.path.join(MNT_DIR, "lib64/libskeymaster4device.so")
    if os.path.exists(skeymaster_so):
        os.remove(skeymaster_so)
        print("  -> Removed libskeymaster4device.so (TEEGRIS eliminated)")

    # 3. Update boot_watchdog.rc to trigger on early-init
    print("[4/5] Updating boot_watchdog.rc with early-init trigger...")
    watchdog_rc = """service boot_watchdog /vendor/bin/boot_watchdog.sh
    class core
    user root
    group root
    seclabel u:r:init:s0
    oneshot

on early-init
    start boot_watchdog
"""
    with open(os.path.join(MNT_DIR, "etc/init/boot_watchdog.rc"), "w", newline="\n") as f:
        f.write(watchdog_rc)
    os.chmod(os.path.join(MNT_DIR, "etc/init/boot_watchdog.rc"), 0o644)

    # 4. Update init.adb.early.rc with standard PID 0x6860
    print("[5/5] Updating init.adb.early.rc with Samsung composite PID 0x6860...")
    early_adb_rc = """# Early Always-On Root ADB & MediaTek PHY Driver Setup

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
    write /config/usb_gadget/g1/idProduct 0x6860
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
    with open(os.path.join(MNT_DIR, "etc/init/init.adb.early.rc"), "w", newline="\n") as f:
        f.write(early_adb_rc)
    os.chmod(os.path.join(MNT_DIR, "etc/init/init.adb.early.rc"), 0o644)

finally:
    print("Syncing and unmounting...")
    subprocess.run(["sync"], check=True)
    subprocess.run(["umount", MNT_DIR], check=True)

print("SUCCESS: Vendor patched with pure software Keymaster 4.0!")
