import os
import shutil
import subprocess

RAW_VEN = "/build/vendor_aosp_raw.img"
MNT_DIR = "/build/mnt_aosp_vendor"
SRC_MODULES_DIR = "/mnt/i/AOSP_Project/modules"
STRIP_TOOL = "/build/toolchains/clang-r383902/bin/llvm-strip"
IDC_SRC = "/mnt/i/AOSP_Project/touch_fix/sec_touchscreen.idc"
TSP_SH_SRC = "/mnt/i/AOSP_Project/touch_fix/tsp_init.sh"
OUT_VEN = "/mnt/i/AOSP_Project/vendor.img"

MODULE_NAMES = [
    "connfem.ko",
    "wmt_drv.ko",
    "wmt_chrdev_wifi.ko",
    "bt_drv_connac1x.ko",
    "gps_drv.ko",
    "fmradio_drv_mt6631_6635.ko",
    "wlan_drv_gen4m.ko",
    "met.ko",
    "fpsgo.ko"
]

print("==========================================================")
print("  Building Optimized AOSP A13 Vendor for SM-M326B")
print("==========================================================")

print("[1/8] Unsparsing base vendor image...")
if os.path.exists(MNT_DIR):
    subprocess.run(["umount", "-f", MNT_DIR], stderr=subprocess.DEVNULL)
    shutil.rmtree(MNT_DIR, ignore_errors=True)
os.makedirs(MNT_DIR, exist_ok=True)

if os.path.exists(RAW_VEN):
    os.remove(RAW_VEN)

subprocess.run(["/mnt/i/AOSP_Project/tools/simg2img", "/build/vendor_working.img", RAW_VEN], check=True)
subprocess.run(["e2fsck", "-y", "-f", RAW_VEN], check=False)
subprocess.run(["resize2fs", RAW_VEN], check=True)

print("[2/8] Mounting raw vendor image...")
subprocess.run(["mount", "-o", "loop,rw", RAW_VEN, MNT_DIR], check=True)

try:
    # 1. Inject and strip 9 MediaTek kernel modules
    print("[3/8] Injecting 9 source-compiled MediaTek kernel modules...")
    ven_mod_dir = os.path.join(MNT_DIR, "lib/modules")
    os.makedirs(ven_mod_dir, exist_ok=True)
    for f in os.listdir(ven_mod_dir):
        if f.endswith(".ko"):
            os.remove(os.path.join(ven_mod_dir, f))

    for mod in MODULE_NAMES:
        src = os.path.join(SRC_MODULES_DIR, mod)
        dst = os.path.join(ven_mod_dir, mod)
        shutil.copy2(src, dst)
        if mod != "fpsgo.ko":
            subprocess.run([STRIP_TOOL, "--strip-unneeded", dst], check=True)
        os.chmod(dst, 0o644)
        print(f"  -> Injected & stripped {mod}: {os.path.getsize(dst):,} bytes")

    # Write modules.load & modules.dep
    with open(os.path.join(ven_mod_dir, "modules.load"), "w") as f:
        f.write("\n".join(MODULE_NAMES) + "\n")
    os.chmod(os.path.join(ven_mod_dir, "modules.load"), 0o644)

    dep_content = (
        "bt_drv_connac1x.ko: wmt_drv.ko\n"
        "connfem.ko:\n"
        "fmradio_drv_mt6631_6635.ko: wmt_drv.ko\n"
        "fpsgo.ko:\n"
        "gps_drv.ko: wmt_drv.ko\n"
        "met.ko:\n"
        "wlan_drv_gen4m.ko: wmt_chrdev_wifi.ko connfem.ko wmt_drv.ko\n"
        "wmt_chrdev_wifi.ko: wmt_drv.ko\n"
        "wmt_drv.ko:\n"
    )
    with open(os.path.join(ven_mod_dir, "modules.dep"), "w") as f:
        f.write(dep_content)
    os.chmod(os.path.join(ven_mod_dir, "modules.dep"), 0o644)

    # 2. Inject Touchscreen IDC Configuration
    print("[4/8] Installing Ilitek TDDI Touch IDC (sec_touchscreen.idc)...")
    idc_dir = os.path.join(MNT_DIR, "usr/idc")
    os.makedirs(idc_dir, exist_ok=True)
    shutil.copy2(IDC_SRC, os.path.join(idc_dir, "sec_touchscreen.idc"))
    os.chmod(os.path.join(idc_dir, "sec_touchscreen.idc"), 0o644)

    # 3. Inject Touch Initializer & Backlight Service
    print("[5/8] Installing Touch & Backlight Initializer Service...")
    ven_bin = os.path.join(MNT_DIR, "bin")
    os.makedirs(ven_bin, exist_ok=True)
    shutil.copy2(TSP_SH_SRC, os.path.join(ven_bin, "tsp_init.sh"))
    os.chmod(os.path.join(ven_bin, "tsp_init.sh"), 0o755)

    tsp_rc = """# Samsung Galaxy M32 5G Touch & Backlight Service
service tsp_init /vendor/bin/tsp_init.sh
    class early-boot
    user root
    group root
    oneshot
"""
    with open(os.path.join(MNT_DIR, "etc/init/init.tsp.rc"), "w") as f:
        f.write(tsp_rc)
    os.chmod(os.path.join(MNT_DIR, "etc/init/init.tsp.rc"), 0o644)

    # 4. Disable Samsung-Only Crashing Daemons & Blocking TEEGRIS wait_for_prop
    print("[6/8] Disabling Samsung-Only Crashing Daemons & Blocking TEEGRIS...")
    crash_rcs = [
        "etc/init/face-default-sec.rc",
        "etc/init/lights-default-sec.rc",
        "etc/init/samsung.software.media.c2@1.0-service.rc",
        "etc/init/vendor.samsung.hardware.vibrator-default.rc",
        "etc/init/vendor.samsung.hardware.security.hdcp.wifidisplay-default.rc",
        "etc/init/emservice.rc",
        "etc/init/pa_daemon_teegris.rc"
    ]
    for rc in crash_rcs:
        p = os.path.join(MNT_DIR, rc)
        if os.path.exists(p):
            lines = open(p).readlines()
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if line.startswith("service "):
                    new_lines.append("    disabled\n")
            open(p, "w").writelines(new_lines)
            print(f"  -> Disabled crasher: {rc}")

    teegris_rc = os.path.join(MNT_DIR, "etc/init/teegris_v4.rc")
    if os.path.exists(teegris_rc):
        t_content = open(teegris_rc).read()
        t_content = t_content.replace("wait_for_prop vendor.tzdaemon Ready", "setprop vendor.tzdaemon Ready")
        t_content = t_content.replace("wait_for_prop vendor.tzts_daemon Ready", "setprop vendor.tzts_daemon Ready")
        open(teegris_rc, "w").write(t_content)
        print("  -> Neutered blocking wait_for_prop in teegris_v4.rc")

    # 5. Inject Software Keymaster & Gatekeeper HALs
    print("[6/8] Injecting Software Keymaster @4.0 & Gatekeeper @1.0 HALs...")
    L20_VEN = "/build/lineage20/out/target/product/m326b/vendor"
    
    # 5a. Binaries
    hw_dir = os.path.join(MNT_DIR, "bin/hw")
    os.makedirs(hw_dir, exist_ok=True)
    for bin_name in ["android.hardware.keymaster@4.0-service", "android.hardware.gatekeeper@1.0-service"]:
        src_b = os.path.join(L20_VEN, "bin/hw", bin_name)
        dst_b = os.path.join(hw_dir, bin_name)
        if os.path.exists(src_b):
            shutil.copy2(src_b, dst_b)
            os.chmod(dst_b, 0o755)
            print(f"  -> Injected binary: {bin_name}")

    # 5b. Init RC scripts
    for rc_name in ["android.hardware.keymaster@4.0-service.rc", "android.hardware.gatekeeper@1.0-service.rc"]:
        src_rc = os.path.join(L20_VEN, "etc/init", rc_name)
        dst_rc = os.path.join(MNT_DIR, "etc/init", rc_name)
        if os.path.exists(src_rc):
            shutil.copy2(src_rc, dst_rc)
            os.chmod(dst_rc, 0o644)
            print(f"  -> Injected init rc: {rc_name}")

    # 5c. Shared libraries
    v_lib64 = os.path.join(MNT_DIR, "lib64")
    os.makedirs(v_lib64, exist_ok=True)
    v_lib64_hw = os.path.join(v_lib64, "hw")
    os.makedirs(v_lib64_hw, exist_ok=True)

    KM_LIBS = [
        "libskeymaster4device.so", "libpuresoftkeymasterdevice.so", "libkeymaster4.so",
        "libkeymaster4support.so", "libkeymaster4_1support.so", "android.hardware.keymaster@4.0.so",
        "android.hardware.keymaster@4.1.so", "libkeymaster_messages.so", "libkeymaster_portable.so",
        "libkeymaster_helper.so", "vendor.mediatek.hardware.keymaster_attestation@1.1.so",
        "vendor.mediatek.hardware.keymaster_attestation@1.0.so", "android.hardware.gatekeeper@1.0.so"
    ]
    for lib in KM_LIBS:
        src_l = os.path.join(L20_VEN, "lib64", lib)
        if os.path.exists(src_l):
            shutil.copy2(src_l, os.path.join(v_lib64, lib))
            os.chmod(os.path.join(v_lib64, lib), 0o644)

    # hw subfolder libs
    for hw_lib in ["gatekeeper.mt6853.so", "android.hardware.gatekeeper@1.0-impl.so"]:
        src_hl = os.path.join(L20_VEN, "lib64/hw", hw_lib)
        if os.path.exists(src_hl):
            shutil.copy2(src_hl, os.path.join(v_lib64_hw, hw_lib))
            os.chmod(os.path.join(v_lib64_hw, hw_lib), 0o644)
    print("  -> Injected all Keymaster and Gatekeeper runtime libraries")

    # 6. Inject Boot-Level USB ADB & MediaTek musb-hdrc PHY Initialization
    print("[6.5/8] Injecting Boot-Level USB ADB & MediaTek musb-hdrc Config...")
    early_adb_rc = """# Early Always-On Root ADB & MediaTek PHY Driver Setup

on early-init
    setprop sys.usb.controller "musb-hdrc"
    setprop vendor.usb.controller "musb-hdrc"
    setprop sys.usb.configfs 1

on post-fs
    # Force MediaTek PHY into peripheral/device mode (cmode 2) so host PC detects USB
    write /sys/class/udc/musb-hdrc/device/cmode 2
    write /sys/class/udc/musb-hdrc/device/saving 0

on boot
    write /sys/class/udc/musb-hdrc/device/cmode 2
    write /sys/class/udc/musb-hdrc/device/saving 0
    setprop sys.usb.configfs 1
    setprop sys.usb.controller "musb-hdrc"
    setprop vendor.usb.controller "musb-hdrc"
    # Trigger USB gadget state transition to ADB
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
    with open(os.path.join(MNT_DIR, "etc/init/init.adb.early.rc"), "w") as f:
        f.write(early_adb_rc)
    os.chmod(os.path.join(MNT_DIR, "etc/init/init.adb.early.rc"), 0o644)

    # 6. Inject Autonomous 90-Second Boot Watchdog
    print("[6.7/8] Injecting Autonomous 90-Second Boot Watchdog...")
    watchdog_sh = """#!/system/bin/sh
# Autonomous Boot Fail-Safe Watchdog for SM-M326B
# Auto-reboots straight to TWRP Recovery if system hangs or fails to reach Launcher3

TIMEOUT=90
ELAPSED=0

echo "[boot_watchdog] Watchdog armed. 90-second countdown initialized." > /dev/kmsg

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
setprop sys.powerctl reboot,recovery
/system/bin/reboot recovery 2>/dev/null
/vendor/bin/reboot recovery 2>/dev/null
sleep 5
echo b > /proc/sysrq-trigger
"""
    with open(os.path.join(MNT_DIR, "bin/boot_watchdog.sh"), "w") as f:
        f.write(watchdog_sh)
    os.chmod(os.path.join(MNT_DIR, "bin/boot_watchdog.sh"), 0o755)

    watchdog_rc = """service boot_watchdog /vendor/bin/boot_watchdog.sh
    user root
    group root
    oneshot
    seclabel u:r:init:s0

on post-fs-data
    start boot_watchdog
"""
    with open(os.path.join(MNT_DIR, "etc/init/boot_watchdog.rc"), "w") as f:
        f.write(watchdog_rc)
    os.chmod(os.path.join(MNT_DIR, "etc/init/boot_watchdog.rc"), 0o644)

    # Update vendor build.prop for early ADB & permissive debug
    vprop = os.path.join(MNT_DIR, "build.prop")
    if not os.path.exists(vprop):
        vprop = os.path.join(MNT_DIR, "vendor/build.prop")
    
    if os.path.exists(vprop):
        with open(vprop, "r", encoding="utf-8", errors="ignore") as f:
            vlines = f.readlines()
        clean_lines = [l for l in vlines if not any(k in l for k in [
            "sys.usb.controller", "vendor.usb.controller", "persist.sys.usb.config",
            "ro.adb.secure", "ro.secure", "ro.debuggable"
        ])]
        clean_lines.append("\n# Boot-Level Root USB ADB Configuration\n")
        clean_lines.append("sys.usb.controller=musb-hdrc\n")
        clean_lines.append("vendor.usb.controller=musb-hdrc\n")
        clean_lines.append("persist.sys.usb.config=adb\n")
        clean_lines.append("ro.adb.secure=0\n")
        clean_lines.append("ro.secure=0\n")
        clean_lines.append("ro.debuggable=1\n")
        clean_lines.append("persist.sys.enable_rescue=0\n")
        clean_lines.append("persist.sys.disable_rescue=true\n")
        with open(vprop, "w", encoding="utf-8") as f:
            f.writelines(clean_lines)
        print("  -> Injected boot-level USB ADB into vendor build.prop")

finally:
    print("[7/8] Syncing and unmounting...")
    subprocess.run(["sync"], check=True)
    subprocess.run(["umount", MNT_DIR], check=True)
    shutil.rmtree(MNT_DIR, ignore_errors=True)

print("[8/8] Converting to sparse vendor.img...")
subprocess.run(["/mnt/i/AOSP_Project/tools/img2simg", RAW_VEN, OUT_VEN], check=True)
if os.path.exists(RAW_VEN):
    os.remove(RAW_VEN)

ven_size = os.path.getsize(OUT_VEN)
print(f"SUCCESS: AOSP Vendor created at {OUT_VEN} ({ven_size:,} bytes)")
