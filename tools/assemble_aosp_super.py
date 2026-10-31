import subprocess
import os

LPMAKE = "/mnt/i/AOSP_Project/tools/lpmake"
OUT_SUPER = "/mnt/i/AOSP_Project/super.img"

SYS_IMG = "/mnt/i/AOSP_Project/system.img"
VEN_IMG = "/mnt/i/AOSP_Project/vendor.img"
PROD_IMG = "/mnt/i/AOSP_Project/product.img"
ODM_IMG = "/mnt/i/AOSP_Project/odm.img"

# Exact unsparsed sizes
SYS_SIZE = 2936012800
VEN_SIZE = 984141824
PROD_SIZE = 590872576
ODM_SIZE = 43368448

cmd = [
    LPMAKE,
    "--device-size=7864320000",
    "--metadata-size=65536",
    "--metadata-slots=2",
    "-o", OUT_SUPER,
    "-S",
    f"-p", f"system:readonly:{SYS_SIZE}:main",
    f"-i", f"system={SYS_IMG}",
    f"-p", f"vendor:readonly:{VEN_SIZE}:main",
    f"-i", f"vendor={VEN_IMG}",
    f"-p", f"product:readonly:{PROD_SIZE}:main",
    f"-i", f"product={PROD_IMG}",
    f"-p", f"odm:readonly:{ODM_SIZE}:main",
    f"-i", f"odm={ODM_IMG}",
    "-g", "main:7860125696",
    "--super-name=super"
]

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = "/build/lineage20/out/host/linux-x86/lib64:" + env.get("LD_LIBRARY_PATH", "")

print("==========================================================")
print("  Assembling Samsung Galaxy M32 5G AOSP super.img")
print("==========================================================")
subprocess.run(cmd, env=env, check=True)
super_sz = os.path.getsize(OUT_SUPER)
print(f"SUCCESS: super.img created ({super_sz:,} bytes / {super_sz / (1024*1024*1024):.2f} GB)")
