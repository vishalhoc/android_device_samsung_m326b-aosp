import os
import shutil
import subprocess

WORK_DIR = "/build/early_rd"
BASE_RD = "/build/ref_boot_unpack/ramdisk"
OUT_RD = "/mnt/i/AOSP_Project/kernel/early_ramdisk.gz"
REC_ROOT = "/build/lineage20/out/target/product/m326b/recovery/root"

print("==========================================================")
print("  Assembling First-Stage Early ADB Ramdisk for SM-M326B")
print("==========================================================")

if os.path.exists(WORK_DIR):
    shutil.rmtree(WORK_DIR)
os.makedirs(WORK_DIR, exist_ok=True)

# 1. Unpack base ramdisk
print("[1/6] Unpacking base first-stage ramdisk...")
cmd_unpack = f"cd {WORK_DIR} && gzip -dc {BASE_RD} | cpio -idm 2>/dev/null"
subprocess.run(cmd_unpack, shell=True, check=True)

# 2. Swap init with early_init
print("[2/6] Swapping init with static early_init...")
orig_init = os.path.join(WORK_DIR, "init")
real_init = os.path.join(WORK_DIR, "init.real")
if os.path.exists(orig_init):
    os.rename(orig_init, real_init)
    os.chmod(real_init, 0o755)

shutil.copy2("/tmp/early_init", orig_init)
os.chmod(orig_init, 0o755)

# 3. Add system/bin tools
print("[3/6] Embedding adbd, linker64, toybox, and sh...")
sys_bin = os.path.join(WORK_DIR, "system/bin")
os.makedirs(sys_bin, exist_ok=True)

shutil.copy2(os.path.join(REC_ROOT, "system/bin/adbd"), os.path.join(sys_bin, "adbd"))
shutil.copy2(os.path.join(REC_ROOT, "system/bin/linker64"), os.path.join(sys_bin, "linker64"))
shutil.copy2(os.path.join(REC_ROOT, "system/bin/toybox"), os.path.join(sys_bin, "toybox"))

for tool in ["sh", "getprop", "setprop", "dmesg", "cat", "ls", "ps", "kill", "reboot", "sync", "sleep", "echo"]:
    sym_path = os.path.join(sys_bin, tool)
    if os.path.exists(sym_path) or os.path.islink(sym_path):
        os.remove(sym_path)
    os.symlink("toybox", sym_path)

# 4. Add system/lib64
print("[4/6] Embedding runtime dynamic libraries...")
sys_lib64 = os.path.join(WORK_DIR, "system/lib64")
os.makedirs(sys_lib64, exist_ok=True)

NEEDED_LIBS = [
    "libadbd_auth.so", "libadbd_fs.so", "libbase.so", "libc++.so",
    "libc.so", "libcrypto.so", "libcrypto_utils.so", "libdl.so",
    "liblog.so", "liblogwrap.so", "libm.so", "libselinux.so",
    "libprocessgroup.so", "libz.so"
]

for lib in NEEDED_LIBS:
    src_lib = os.path.join(REC_ROOT, "system/lib64", lib)
    if os.path.exists(src_lib):
        shutil.copy2(src_lib, os.path.join(sys_lib64, lib))
    else:
        print(f"[-] Warning: missing library {lib}")

# 5. Add /sbin symlink for convenience
sbin_dir = os.path.join(WORK_DIR, "sbin")
os.makedirs(sbin_dir, exist_ok=True)
for tool in ["adbd", "toybox", "sh"]:
    s_path = os.path.join(sbin_dir, tool)
    if os.path.exists(s_path) or os.path.islink(s_path):
        os.remove(s_path)
    os.symlink(f"/system/bin/{tool}", s_path)

# 6. Repack ramdisk
print("[5/6] Repacking ramdisk cpio.gz...")
if os.path.exists(OUT_RD):
    os.remove(OUT_RD)

cmd_repack = f"cd {WORK_DIR} && find . | cpio -H newc -o 2>/dev/null | gzip -9 > {OUT_RD}"
subprocess.run(cmd_repack, shell=True, check=True)

rd_size = os.path.getsize(OUT_RD)
print(f"[6/6] SUCCESS: Early ADB ramdisk generated at {OUT_RD} ({rd_size:,} bytes / {rd_size / (1024*1024):.2f} MB)")
