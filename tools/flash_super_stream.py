import subprocess
import time
import os
import sys

ADB = r"C:\Users\visha\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEV = "RZCR904AE4Z"
SUPER_IMG = r"I:\AOSP_Project\super.img"

print("==========================================================")
print("  Streaming super.img directly into sparse_flash on Device")
print("==========================================================")

super_sz = os.path.getsize(SUPER_IMG)
print(f"[*] super.img size: {super_sz:,} bytes ({super_sz / (1024*1024*1024):.2f} GB)")

# Check ADB connection
out = subprocess.run([ADB, "-s", DEV, "devices"], capture_output=True, text=True).stdout
if DEV not in out:
    print(f"[-] ERROR: Device {DEV} not found in adb devices!")
    sys.exit(1)

# Unmount any existing dynamic partition mounts
print("[*] Unmounting dynamic logical partitions on device...")
subprocess.run([ADB, "-s", DEV, "shell", "umount /system /vendor /product /odm /system_root 2>/dev/null || true"])

# Start sparse_flash process with exec-in
print("[*] Starting sparse_flash stream via adb exec-in...")
start_t = time.time()
cmd = [ADB, "-s", DEV, "exec-in", "/tmp/sparse_flash", "/dev/block/by-name/super"]

with open(SUPER_IMG, "rb") as f_img:
    proc = subprocess.Popen(cmd, stdin=f_img, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()

elapsed = time.time() - start_t
speed = (super_sz / (1024*1024)) / elapsed if elapsed > 0 else 0

print(stdout.decode("utf-8", errors="ignore"))
if stderr:
    print("STDERR:", stderr.decode("utf-8", errors="ignore"))

print(f"[*] Process exited with code: {proc.returncode}")
print(f"[*] Streamed {super_sz:,} bytes in {elapsed:.2f}s ({speed:.2f} MB/s)")

if proc.returncode == 0:
    print("==========================================================")
    print("  SUCCESS: super partition flashed successfully!")
    print("==========================================================")
else:
    print("[-] Flashing failed!")
    sys.exit(1)
