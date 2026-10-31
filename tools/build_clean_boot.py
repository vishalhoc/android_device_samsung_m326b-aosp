import subprocess
import os

KERNEL = "/build/check_boot_unpack/kernel"
RAMDISK = "/build/check_boot_unpack/ramdisk"
DTB = "/build/check_boot_unpack/dtb"
RAW_BOOT = "/mnt/i/AOSP_Project/kernel/boot_raw.img"
FINAL_BOOT = "/mnt/i/AOSP_Project/kernel/boot.img"
AVBTOOL = "/mnt/i/AOSP_Project/tools/avbtool"
KEY = "/mnt/i/AOSP_Project/tools/testkey_rsa4096.pem"

print("==========================================================")
print("  Assembling Samsung Galaxy M32 5G Clean AOSP boot.img")
print("==========================================================")

cmd_mkbootimg = [
    "python3", "/build/lineage20/system/tools/mkbootimg/mkbootimg.py",
    "--kernel", KERNEL,
    "--ramdisk", RAMDISK,
    "--dtb", DTB,
    "--base", "0x40000000",
    "--kernel_offset", "0x00080000",
    "--ramdisk_offset", "0x07c80000",
    "--tags_offset", "0x0bc80000",
    "--dtb_offset", "0x0bc80000",
    "--header_version", "2",
    "--pagesize", "2048",
    "--os_version", "13.0.0",
    "--os_patch_level", "2026-02",
    "--board", "SRPTF26A012",
    "--cmdline", "bootopt=64S3,32N2,64N2 loop.max_part=7 buildvariant=userdebug androidboot.selinux=permissive androidboot.veritymode=disabled androidboot.force_normal_boot=1 androidboot.fstab_suffix=mt6853 androidboot.hardware=mt6853 androidboot.usbcontroller=musb-hdrc",
    "-o", RAW_BOOT
]

print("[1/3] Running mkbootimg...")
subprocess.run(cmd_mkbootimg, check=True)

print("[2/3] Appending Samsung SEANDROIDENFORCE magic footer...")
with open(RAW_BOOT, "ab") as f:
    f.write(b"SEANDROIDENFORCE")

print("[3/3] Signing with avbtool to exact 32MB (33,554,432 bytes)...")
cmd_avb = [
    "python3", AVBTOOL, "add_hash_footer",
    "--image", RAW_BOOT,
    "--partition_size", "33554432",
    "--partition_name", "boot",
    "--key", KEY,
    "--algorithm", "SHA256_RSA4096"
]
subprocess.run(cmd_avb, check=True)

os.replace(RAW_BOOT, FINAL_BOOT)
final_size = os.path.getsize(FINAL_BOOT)
print(f"SUCCESS: {FINAL_BOOT} generated ({final_size} bytes)")
assert final_size == 33554432, f"Error: expected 33554432, got {final_size}"
