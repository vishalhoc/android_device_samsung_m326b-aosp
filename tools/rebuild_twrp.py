import os
import shutil
import subprocess

TWRP_DIR = "/build/twrp_build_clean"
RD_DIR = os.path.join(TWRP_DIR, "ramdisk")
OUT_CPIONAME = os.path.join(TWRP_DIR, "new_ramdisk.img")
OUT_UNSIGNED = os.path.join(TWRP_DIR, "recovery_unsigned.img")
OUT_SIGNED = os.path.join(TWRP_DIR, "recovery_signed.img")
FINAL_RECOVERY = "/mnt/i/AOSP_Project/recovery/recovery.img"

MKBOOTIMG = "/build/lineage20/system/tools/mkbootimg/mkbootimg.py"
AVBTOOL = "/mnt/i/AOSP_Project/tools/avbtool"
KEY = "/mnt/i/AOSP_Project/tools/testkey_rsa4096.pem"

print("==========================================================")
print("  Permanently Fixing TWRP ADB USB Reset & Rebuilding TWRP")
print("==========================================================")

# 1. Update init.recovery.mt6853.rc
print("[1/6] Patching init.recovery.mt6853.rc for permanent USB & VM stability...")
rc_path = os.path.join(RD_DIR, "init.recovery.mt6853.rc")
rc_content = """# init.recovery.mt6853.rc — Samsung Galaxy M32 5G (SM-M326B)
on init
    setprop sys.usb.configfs 1
    setprop sys.usb.controller "musb-hdrc"
    setprop vendor.usb.controller "musb-hdrc"
    setprop sys.usb.ffs.aio_compat 1
    # Force MediaTek USB PHY into full peripheral mode (cmode 3) & disable power throttling
    write /sys/class/udc/musb-hdrc/device/cmode 3
    write /sys/class/udc/musb-hdrc/device/saving 0
    write /sys/class/udc/musb-hdrc/power/control on
    # Tune Linux VM page writeback to prevent cache balloons and IO lockups during multi-GB transfers
    write /proc/sys/vm/dirty_background_ratio 5
    write /proc/sys/vm/dirty_ratio 10
    write /proc/sys/vm/vfs_cache_pressure 50
    write /proc/sys/vm/swappiness 0
    # Set display backlight
    write /sys/class/leds/lcd-backlight/brightness 200
    write /sys/devices/platform/panel/panel_drv/backlight/panel/brightness 200

on fs
    write /sys/class/udc/musb-hdrc/device/cmode 3
    write /sys/class/udc/musb-hdrc/device/saving 0
    write /sys/class/udc/musb-hdrc/power/control on
    start adbd

on post-fs
    wait /dev/block/mmcblk0boot0 2
    symlink /dev/block/sda /dev/block/mmcblk0boot0

service tsp_keepalive /system/bin/tsp_keepalive.sh
    user root
    group root
    seclabel u:r:recovery:s0

service teegris_decrypt /system/bin/sh /system/bin/start_teegris_decrypt.sh
    user root
    group root
    seclabel u:r:recovery:s0

on boot
    start tsp_keepalive
    start teegris_decrypt

on property:sys.powerctl=*
    powerctl ${sys.powerctl}
"""
with open(rc_path, "w", newline="\n") as f:
    f.write(rc_content)
os.chmod(rc_path, 0o755)

# 2. Patch tsp_keepalive.sh
print("[2/6] Adding hardware watchdog kicks & USB keepalive to tsp_keepalive.sh...")
tsp_path = os.path.join(RD_DIR, "system/bin/tsp_keepalive.sh")
with open(tsp_path, "r", encoding="utf-8") as f:
    tsp_code = f.read()

# Add watchdog & usb keepalive to the loop
loop_patch = """
    # Keep USB PHY powered on and prevent autosuspend / reset during long ADB transfers
    echo 0 > /sys/class/udc/musb-hdrc/device/saving 2>/dev/null || true
    echo 3 > /sys/class/udc/musb-hdrc/device/cmode 2>/dev/null || true
    echo on > /sys/class/udc/musb-hdrc/power/control 2>/dev/null || true
    echo -1 > /sys/module/usbcore/parameters/autosuspend 2>/dev/null || true
    # Kick hardware watchdogs so long I/O operations never trigger reset
    echo V > /dev/watchdog 2>/dev/null || true
    echo 1 > /sys/devices/virtual/misc/mrdump/wdt_kick 2>/dev/null || true
"""
if "musb-hdrc/device/saving" not in tsp_code:
    tsp_code = tsp_code.replace("loop_count=$((loop_count + 1))", loop_patch + "\n    loop_count=$((loop_count + 1))")
    with open(tsp_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(tsp_code)
os.chmod(tsp_path, 0o755)

# 3. Patch default.prop and prop.default
print("[3/6] Injecting stable USB ADB properties...")
for pfile in ["default.prop", "prop.default"]:
    pp = os.path.join(RD_DIR, pfile)
    if os.path.exists(pp):
        with open(pp, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        clean = [l for l in lines if not any(k in l for k in [
            "sys.usb.config", "persist.sys.usb.config", "sys.usb.controller",
            "vendor.usb.controller", "tw_mtp_enabled"
        ])]
        clean.append("\n# Permanent USB ADB Stability Config\n")
        clean.append("persist.sys.usb.config=adb\n")
        clean.append("sys.usb.config=adb\n")
        clean.append("sys.usb.controller=musb-hdrc\n")
        clean.append("vendor.usb.controller=musb-hdrc\n")
        clean.append("tw_mtp_enabled=0\n")
        with open(pp, "w", encoding="utf-8", newline="\n") as f:
            f.writelines(clean)

# 4. Patch twres/ui.xml
print("[4/6] Setting tw_mtp_enabled=0 in twres/ui.xml...")
ui_xml = os.path.join(RD_DIR, "twres/ui.xml")
if os.path.exists(ui_xml):
    with open(ui_xml, "r", encoding="utf-8", errors="ignore") as f:
        xml_text = f.read()
    xml_text = xml_text.replace('name="tw_mtp_enabled" default="1"', 'name="tw_mtp_enabled" default="0"')
    xml_text = xml_text.replace('name="tw_has_mtp" default="1"', 'name="tw_has_mtp" default="0"')
    with open(ui_xml, "w", encoding="utf-8", newline="\n") as f:
        f.write(xml_text)

# 5. Repack ramdisk
print("[5/6] Repacking TWRP ramdisk...")
if os.path.exists(OUT_CPIONAME):
    os.remove(OUT_CPIONAME)
cmd_cpio = f"cd {RD_DIR} && find . | cpio -H newc -o 2>/dev/null | gzip -9 > {OUT_CPIONAME}"
subprocess.run(cmd_cpio, shell=True, check=True)
rd_sz = os.path.getsize(OUT_CPIONAME)
print(f"  -> Repacked ramdisk: {rd_sz:,} bytes")

# 6. Assemble & Sign Recovery Image
print("[6/6] Assembling & AVB signing recovery image to exact 41,943,040 bytes...")
cmd_mkbootimg = [
    "python3", MKBOOTIMG,
    "--kernel", os.path.join(TWRP_DIR, "kernel.gz"),
    "--ramdisk", OUT_CPIONAME,
    "--dtb", os.path.join(TWRP_DIR, "dtb"),
    "--recovery_dtbo", os.path.join(TWRP_DIR, "recovery_dtbo"),
    "--base", "0x40000000",
    "--kernel_offset", "0x00080000",
    "--ramdisk_offset", "0x07c80000",
    "--tags_offset", "0x0bc80000",
    "--dtb_offset", "0x0bc80000",
    "--header_version", "2",
    "--pagesize", "2048",
    "--os_version", "11.0.0",
    "--os_patch_level", "2026-02",
    "--board", "SRPTF26A012",
    "--cmdline", "bootopt=64S3,32N2,64N2 loop.max_part=7 buildvariant=userdebug androidboot.selinux=permissive androidboot.veritymode=disabled androidboot.force_normal_boot=0 androidboot.fstab_suffix=mt6853 androidboot.hardware=mt6853 androidboot.usbcontroller=musb-hdrc",
    "-o", OUT_UNSIGNED
]
subprocess.run(cmd_mkbootimg, check=True)

with open(OUT_UNSIGNED, "ab") as f:
    f.write(b"SEANDROIDENFORCE")

cmd_avb = [
    "python3", AVBTOOL, "add_hash_footer",
    "--image", OUT_UNSIGNED,
    "--partition_size", "41943040",
    "--partition_name", "recovery",
    "--key", KEY,
    "--algorithm", "SHA256_RSA4096"
]
subprocess.run(cmd_avb, check=True)

shutil.copy2(OUT_UNSIGNED, FINAL_RECOVERY)
final_sz = os.path.getsize(FINAL_RECOVERY)
print(f"==========================================================")
print(f"  SUCCESS: Permanently fixed TWRP Recovery created!")
print(f"  Path: {FINAL_RECOVERY} ({final_sz:,} bytes)")
print(f"==========================================================")
assert final_sz == 41943040, f"Expected 41943040 bytes, got {final_sz}"
