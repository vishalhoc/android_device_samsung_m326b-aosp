import os
import shutil
import subprocess

RAW_VEN = "/build/vendor_test.raw"
MNT_DIR = "/build/mnt_ven_edit"
GENUINE_KM_BIN = "/build/lineage20/out/soong/.intermediates/hardware/interfaces/keymaster/4.0/default/android.hardware.keymaster@4.0-service/android_arm64_armv8-2a_cortex-a76_cfi/android.hardware.keymaster@4.0-service"
SYS_LIB64 = "/build/lineage20/out/target/product/m326b/system/lib64"
PROJECT_MANIFEST = "/mnt/i/AOSP_Project/manifest.xml"

print("==========================================================")
print("  Applying Complete AOSP 13 Boot, HAL & Zygote Fixes")
print("==========================================================")

os.makedirs(MNT_DIR, exist_ok=True)
subprocess.run(["umount", "-f", MNT_DIR], stderr=subprocess.DEVNULL)
print("[1/8] Mounting vendor raw image...")
subprocess.run(["mount", "-o", "loop,rw", RAW_VEN, MNT_DIR], check=True)

try:
    # 1. Install genuine AOSP Keymaster 4.0 binary
    print("[2/8] Installing genuine AOSP software Keymaster 4.0 binary...")
    target_km = os.path.join(MNT_DIR, "bin/hw/android.hardware.keymaster@4.0-service")
    shutil.copy2(GENUINE_KM_BIN, target_km)
    os.chmod(target_km, 0o755)
    print(f"  -> Injected {target_km} ({os.path.getsize(target_km):,} bytes)")

    # 2. Inject missing Treble vendor shared libraries
    print("[3/8] Injecting Treble isolated shared libraries into vendor/lib64/...")
    libs_to_copy = [
        "libcrypto.so",
        "libfmq.so",
        "android.hardware.graphics.common@1.0.so",
        "android.hardware.graphics.common@1.1.so",
        "android.hardware.graphics.common@1.2.so",
        "android.hardware.graphics.mapper@2.0.so",
        "android.hardware.graphics.mapper@2.1.so",
        "android.hardware.graphics.mapper@3.0.so",
        "android.hardware.graphics.mapper@4.0.so"
    ]
    for lib_name in libs_to_copy:
        src = os.path.join(SYS_LIB64, lib_name)
        dst = os.path.join(MNT_DIR, "lib64", lib_name)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            os.chmod(dst, 0o644)
            print(f"  -> Injected {lib_name} ({os.path.getsize(dst):,} bytes)")
        else:
            print(f"  -> WARNING: {src} not found in system lib64")

    # 3. Remove Samsung proprietary skeymaster device
    print("[4/8] Removing Samsung TEEGRIS skeymaster library...")
    skeymaster_so = os.path.join(MNT_DIR, "lib64/libskeymaster4device.so")
    if os.path.exists(skeymaster_so):
        os.remove(skeymaster_so)
        print("  -> Removed libskeymaster4device.so (TEEGRIS eliminated)")

    # Disable crashing gatekeeper hardware service
    gk_rc = os.path.join(MNT_DIR, "etc/init/android.hardware.gatekeeper@1.0-service.rc")
    if os.path.exists(gk_rc):
        with open(gk_rc, "w", newline="\n") as f:
            f.write("""service vendor.gatekeeper-1-0 /vendor/bin/hw/android.hardware.gatekeeper@1.0-service
    interface android.hardware.gatekeeper@1.0::IGatekeeper default
    class hal
    user system
    group system 5678
    disabled
""")
        print("  -> Disabled hardware gatekeeper HAL (gatekeeperd falls back to pure software)")

    # 4. Copy validated VINTF manifest.xml
    print("[5/8] Installing validated VINTF manifest.xml...")
    manifest_dst = os.path.join(MNT_DIR, "etc/vintf/manifest.xml")
    if os.path.exists(PROJECT_MANIFEST):
        shutil.copy2(PROJECT_MANIFEST, manifest_dst)
        os.chmod(manifest_dst, 0o644)
        print("  -> Installed validated manifest.xml with Composer 2.3, DRM 1.4, Health 2.1, Keymaster 4.0")

    # 5. Fix graphics composer service RC
    print("[6/8] Hardening graphics composer service rc...")
    composer_rc = os.path.join(MNT_DIR, "etc/init/android.hardware.graphics.composer@2.3-service.rc")
    if os.path.exists(composer_rc):
        with open(composer_rc, "r") as f:
            c_rc = f.read()
        if "interface android.hardware.graphics.composer@2.3::IComposer default" not in c_rc:
            c_rc = c_rc.replace("class hal animation", "interface android.hardware.graphics.composer@2.3::IComposer default\n    class hal animation")
            with open(composer_rc, "w", newline="\n") as f:
                f.write(c_rc)
            print("  -> Declared IComposer default interface in composer rc")

    # Keymaster RC hardening
    km_rc = os.path.join(MNT_DIR, "etc/init/android.hardware.keymaster@4.0-service.rc")
    with open(km_rc, "w", newline="\n") as f:
        f.write("""service vendor.keymaster-4-0 /vendor/bin/hw/android.hardware.keymaster@4.0-service
    interface android.hardware.keymaster@4.0::IKeymasterDevice default
    class early_hal
    user root
    group root
    seclabel u:r:su:s0
""")
    os.chmod(km_rc, 0o644)

    # 6. Set ro.zygote, ro.sf.lcd_density, and persist.sys.usb.config in build.prop & init.mt6853.rc
    print("[7/8] Configuring Zygote, SurfaceFlinger Display and USB properties...")
    v_build_prop = os.path.join(MNT_DIR, "build.prop")
    with open(v_build_prop, "r") as f:
        bp_lines = f.read()
    bp_lines = bp_lines.replace("persist.sys.usb.config=adb", "persist.sys.usb.config=mtp,adb")
    new_props = []
    if "ro.zygote=" not in bp_lines:
        new_props.append("ro.zygote=zygote64_32")
    if "ro.sf.lcd_density=" not in bp_lines:
        new_props.append("ro.sf.lcd_density=300")
    if "persist.sys.usb.config=" not in bp_lines:
        new_props.append("persist.sys.usb.config=mtp,adb")
    with open(v_build_prop, "w", newline="\n") as f:
        f.write(bp_lines)
        if new_props:
            f.write("\n" + "\n".join(new_props) + "\n")
    print(f"  -> Configured vendor build.prop")

    init_mt = os.path.join(MNT_DIR, "etc/init/hw/init.mt6853.rc")
    if os.path.exists(init_mt):
        with open(init_mt, "r") as f:
            mt_content = f.read()
        if "import /system/etc/init/hw/init.zygote64_32.rc" not in mt_content:
            mt_content = mt_content.replace("# MTK platform .rc configure", "# MTK platform .rc configure\nimport /system/etc/init/hw/init.zygote64_32.rc")
            with open(init_mt, "w", newline="\n") as f:
                f.write(mt_content)
            print("  -> Injected zygote import into init.mt6853.rc")

    # 7. Update early ADB and autonomous watchdog
    print("[8/8] Updating early ADB and autonomous boot watchdog scripts...")
    watchdog_sh = """#!/vendor/bin/sh
TIMEOUT=180
ELAPSED=0

echo "[boot_watchdog] Autonomous 180s Boot Watchdog armed." > /dev/kmsg

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

echo "[boot_watchdog] Branch B: System hang detected after 180s! Auto-rebooting to TWRP Recovery..." > /dev/kmsg
echo -n -e "boot-recovery\\0" > /dev/block/by-name/misc
sync
setprop sys.powerctl reboot,recovery
/system/bin/reboot recovery 2>/dev/null
/vendor/bin/reboot recovery 2>/dev/null
sleep 5
echo b > /proc/sysrq-trigger
"""
    with open(os.path.join(MNT_DIR, "bin/boot_watchdog.sh"), "w", newline="\n") as f:
        f.write(watchdog_sh)
    os.chmod(os.path.join(MNT_DIR, "bin/boot_watchdog.sh"), 0o755)

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

    early_adb_rc = """# Early Always-On Root ADB & MediaTek PHY Driver Setup

on early-init
    write /sys/class/udc/musb-hdrc/device/cmode 3
    write /sys/devices/platform/11201000.mtu3_0/cmode 3
    write /sys/class/udc/musb-hdrc/device/saving 0
    write /sys/class/udc/musb-hdrc/power/control on
    setprop sys.usb.controller "musb-hdrc"
    setprop vendor.usb.controller "musb-hdrc"
    setprop sys.usb.configfs 1
    setprop persist.sys.usb.config mtp,adb

on post-fs
    write /sys/class/udc/musb-hdrc/device/cmode 3
    write /sys/devices/platform/11201000.mtu3_0/cmode 3
    write /sys/class/udc/musb-hdrc/device/saving 0
    write /sys/class/udc/musb-hdrc/power/control on

on boot
    write /sys/class/udc/musb-hdrc/device/cmode 3
    write /sys/devices/platform/11201000.mtu3_0/cmode 3
    write /sys/class/udc/musb-hdrc/device/saving 0
    write /sys/class/udc/musb-hdrc/power/control on
    setprop sys.usb.configfs 1
    setprop sys.usb.controller "musb-hdrc"
    setprop vendor.usb.controller "musb-hdrc"
    setprop sys.usb.config none
    setprop sys.usb.config mtp,adb

on property:sys.usb.config=mtp,adb
    start adbd

on property:sys.usb.config=adb
    start adbd

on property:sys.usb.ffs.ready=1 && property:sys.usb.config=adb
    setprop vendor.usb.state ${sys.usb.config}
    write /config/usb_gadget/g1/idVendor 0x04E8
    write /config/usb_gadget/g1/idProduct 0x6860
    write /config/usb_gadget/g1/configs/b.1/strings/0x409/configuration "mtp_adb"
    rm /config/usb_gadget/g1/configs/b.1/f1
    rm /config/usb_gadget/g1/configs/b.1/f2
    rm /config/usb_gadget/g1/configs/b.1/f3
    rm /config/usb_gadget/g1/configs/b.1/f4
    rm /config/usb_gadget/g1/configs/b.1/f5
    symlink /config/usb_gadget/g1/functions/ffs.mtp /config/usb_gadget/g1/configs/b.1/f1
    symlink /config/usb_gadget/g1/functions/ffs.adb /config/usb_gadget/g1/configs/b.1/f2
    write /config/usb_gadget/g1/UDC "musb-hdrc"
    setprop sys.usb.state ${sys.usb.config}
"""
    with open(os.path.join(MNT_DIR, "etc/init/init.adb.early.rc"), "w", newline="\n") as f:
        f.write(early_adb_rc)
    os.chmod(os.path.join(MNT_DIR, "etc/init/init.adb.early.rc"), 0o644)

    # Set SELinux contexts if setfiles is available
    if shutil.which("setfiles"):
        subprocess.run(["setfiles", "-F", "/build/lineage20/out/target/product/m326b/root/file_contexts", MNT_DIR], stderr=subprocess.DEVNULL)

finally:
    print("Syncing and unmounting...")
    subprocess.run(["sync"], check=True)
    subprocess.run(["umount", MNT_DIR], check=True)

print("SUCCESS: Complete vendor fixes successfully applied!")
