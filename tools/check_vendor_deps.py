import os
import subprocess
import glob

MNT_DIR = "/build/mnt_ven_edit"
RAW_VEN = "/build/vendor_test.raw"
SYS_LIB64 = "/build/lineage20/out/target/product/m326b/system/lib64"

os.makedirs(MNT_DIR, exist_ok=True)
try:
    subprocess.run(["mount", "-o", "rw", RAW_VEN, MNT_DIR], check=True)
    print(f"Mounted {RAW_VEN} at {MNT_DIR}")
    
    ven_lib64 = os.path.join(MNT_DIR, "lib64")
    ven_hw = os.path.join(ven_lib64, "hw")
    
    # Check keymaster service specifically
    km_bin = os.path.join(MNT_DIR, "bin/hw/android.hardware.keymaster@4.0-service")
    print(f"\nChecking dependencies for {km_bin}:")
    
    # Recursive dependency check
    checked = set()
    to_check = [km_bin]
    missing = set()
    
    while to_check:
        curr = to_check.pop(0)
        if curr in checked or not os.path.exists(curr):
            continue
        checked.add(curr)
        
        p = subprocess.run(["readelf", "-d", curr], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in p.stdout.splitlines():
            if "NEEDED" in line and "[" in line and "]" in line:
                lib = line.split("[")[1].split("]")[0]
                # Check where this lib lives
                p_ven = os.path.join(ven_lib64, lib)
                p_hw = os.path.join(ven_hw, lib)
                if os.path.exists(p_ven):
                    if p_ven not in checked:
                        to_check.append(p_ven)
                elif os.path.exists(p_hw):
                    if p_hw not in checked:
                        to_check.append(p_hw)
                elif lib in ["libc.so", "libm.so", "libdl.so", "liblog.so"]:
                    # standard bionic LLNDK
                    pass
                else:
                    # Check if it exists in system/lib64
                    p_sys = os.path.join(SYS_LIB64, lib)
                    sys_exists = os.path.exists(p_sys)
                    print(f"  [MISSING in vendor/lib64] {lib} (needed by {os.path.basename(curr)}) -> in system/lib64: {sys_exists}")
                    missing.add((lib, p_sys if sys_exists else None))

    print(f"\nTotal missing vendor dependencies for Keymaster 4.0: {len(missing)}")
    for lib, sys_path in missing:
        print(f"  * {lib}: {sys_path}")

finally:
    subprocess.run(["umount", MNT_DIR])
    print("Unmounted vendor")
