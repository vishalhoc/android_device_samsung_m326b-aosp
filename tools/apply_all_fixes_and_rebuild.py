import os
import shutil
import subprocess
import sys

BASE_DIR = "/mnt/i/AOSP_Project"
FIXES_DIR = os.path.join(BASE_DIR, "collected_fixes")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
SIMG2IMG = os.path.join(TOOLS_DIR, "simg2img")
IMG2SIMG = os.path.join(TOOLS_DIR, "img2simg")
LPMAKE = os.path.join(TOOLS_DIR, "lpmake")

RAW_VEN = "/build/ven_test.raw"
RAW_PROD = "/build/prod_test.raw"
RAW_SYS_RO = "/build/sys_test.raw"
RAW_SYS_RW = "/build/sys_rw.raw"

MNT_VEN = "/build/mnt_ven_upd"
MNT_PROD = "/build/mnt_prod_upd"
MNT_SYS_RO = "/build/mnt_sys_ro"
MNT_SYS_RW = "/build/mnt_sys_rw"

SYS_EXACT_SIZE = 2936012800

def run_cmd(cmd, check=True):
    print(f"[*] Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)

def update_vendor():
    print("\n==================================================")
    print("  [1/4] Updating Vendor Partition with All Fixes  ")
    print("==================================================")
    os.makedirs(MNT_VEN, exist_ok=True)
    subprocess.run(["umount", "-f", MNT_VEN], stderr=subprocess.DEVNULL)
    
    if not os.path.exists(RAW_VEN):
        print("  -> Unsparsing vendor.img...")
        run_cmd([SIMG2IMG, os.path.join(BASE_DIR, "vendor.img"), RAW_VEN])
        
    run_cmd(["e2fsck", "-y", "-f", RAW_VEN], check=False)
    run_cmd(["resize2fs", RAW_VEN], check=False)
    run_cmd(["mount", "-o", "loop,rw", RAW_VEN, MNT_VEN])
    
    try:
        # 1. 5G SA Unlocked libsec-ril.so
        ril_src = os.path.join(FIXES_DIR, "vendor/lib64/libsec-ril.so")
        ril_dst = os.path.join(MNT_VEN, "lib64/libsec-ril.so")
        shutil.copy2(ril_src, ril_dst)
        os.chmod(ril_dst, 0o644)
        print(f"  [+] Injected 5G SA libsec-ril.so ({os.path.getsize(ril_dst):,} bytes)")

        # 2. Hostapd 5GHz channel validation bypass
        hapd_src = os.path.join(FIXES_DIR, "vendor/bin/hw/hostapd")
        hapd_dst = os.path.join(MNT_VEN, "bin/hw/hostapd")
        shutil.copy2(hapd_src, hapd_dst)
        os.chmod(hapd_dst, 0o755)
        print(f"  [+] Injected 5GHz patched hostapd ({os.path.getsize(hapd_dst):,} bytes)")

        # 3. Light service crash fix
        light_src = os.path.join(FIXES_DIR, "vendor/bin/hw/vendor.samsung.hardware.light-service")
        light_dst = os.path.join(MNT_VEN, "bin/hw/vendor.samsung.hardware.light-service")
        shutil.copy2(light_src, light_dst)
        os.chmod(light_dst, 0o755)
        print(f"  [+] Injected patched vendor.samsung.hardware.light-service")

        # 4. WiFi 5GHz patched module
        wlan_src = os.path.join(FIXES_DIR, "vendor/lib/modules/wlan_drv_gen4m.ko")
        wlan_dst = os.path.join(MNT_VEN, "lib/modules/wlan_drv_gen4m.ko")
        shutil.copy2(wlan_src, wlan_dst)
        os.chmod(wlan_dst, 0o644)
        print(f"  [+] Injected 5GHz patched wlan_drv_gen4m.ko")

        # 5. VINTF manifest.xml
        vintf_src = os.path.join(FIXES_DIR, "vendor/etc/vintf/manifest.xml")
        vintf_dst = os.path.join(MNT_VEN, "etc/vintf/manifest.xml")
        shutil.copy2(vintf_src, vintf_dst)
        os.chmod(vintf_dst, 0o644)
        print(f"  [+] Injected updated manifest.xml")

        # 6. Early USB gadget & root ADB rc
        adb_rc_src = os.path.join(FIXES_DIR, "vendor/etc/init/init.adb.early.rc")
        adb_rc_dst = os.path.join(MNT_VEN, "etc/init/init.adb.early.rc")
        shutil.copy2(adb_rc_src, adb_rc_dst)
        os.chmod(adb_rc_dst, 0o644)
        print(f"  [+] Injected init.adb.early.rc")

        # 7. Boot watchdog
        wd_sh_src = os.path.join(FIXES_DIR, "vendor/bin/boot_watchdog.sh")
        wd_sh_dst = os.path.join(MNT_VEN, "bin/boot_watchdog.sh")
        shutil.copy2(wd_sh_src, wd_sh_dst)
        os.chmod(wd_sh_dst, 0o755)

        wd_rc_src = os.path.join(FIXES_DIR, "vendor/etc/init/boot_watchdog.rc")
        wd_rc_dst = os.path.join(MNT_VEN, "etc/init/boot_watchdog.rc")
        shutil.copy2(wd_rc_src, wd_rc_dst)
        os.chmod(wd_rc_dst, 0o644)
        print(f"  [+] Injected boot_watchdog service")

    finally:
        print("  -> Syncing and unmounting vendor...")
        run_cmd(["sync"])
        run_cmd(["umount", MNT_VEN])

    print("  -> Converting to sparse vendor.img...")
    run_cmd([IMG2SIMG, RAW_VEN, os.path.join(BASE_DIR, "vendor.img")])
    print(f"  [+] vendor.img successfully updated! ({os.path.getsize(os.path.join(BASE_DIR, 'vendor.img')):,} bytes)")

def update_product():
    print("\n===================================================")
    print("  [2/4] Updating Product Partition with All Fixes  ")
    print("===================================================")
    os.makedirs(MNT_PROD, exist_ok=True)
    subprocess.run(["umount", "-f", MNT_PROD], stderr=subprocess.DEVNULL)
    
    if not os.path.exists(RAW_PROD):
        print("  -> Unsparsing product.img...")
        run_cmd([SIMG2IMG, os.path.join(BASE_DIR, "product.img"), RAW_PROD])
        
    run_cmd(["e2fsck", "-y", "-f", RAW_PROD], check=False)
    run_cmd(["mount", "-o", "loop,rw", RAW_PROD, MNT_PROD])
    
    try:
        # 1. 5GHz WiFi overlay
        overlay_dir = os.path.join(MNT_PROD, "overlay")
        os.makedirs(overlay_dir, exist_ok=True)
        wifi_apk_src = os.path.join(FIXES_DIR, "system/product/overlay/wifi-5g-overlay.apk")
        wifi_apk_dst = os.path.join(overlay_dir, "wifi-5g-overlay.apk")
        shutil.copy2(wifi_apk_src, wifi_apk_dst)
        os.chmod(wifi_apk_dst, 0o644)
        print(f"  [+] Injected wifi-5g-overlay.apk into product/overlay")

        # 2. 5G NR APN settings
        apns_src = os.path.join(FIXES_DIR, "system/product/etc/apns-conf.xml")
        apns_dst = os.path.join(MNT_PROD, "etc/apns-conf.xml")
        shutil.copy2(apns_src, apns_dst)
        os.chmod(apns_dst, 0o644)
        print(f"  [+] Injected 5G NR apns-conf.xml into product/etc")

    finally:
        print("  -> Syncing and unmounting product...")
        run_cmd(["sync"])
        run_cmd(["umount", MNT_PROD])

    print("  -> Converting to sparse product.img...")
    run_cmd([IMG2SIMG, RAW_PROD, os.path.join(BASE_DIR, "product.img")])
    print(f"  [+] product.img successfully updated! ({os.path.getsize(os.path.join(BASE_DIR, 'product.img')):,} bytes)")

def update_system():
    print("\n==================================================")
    print("  [3/4] Updating System Partition with All Fixes  ")
    print("==================================================")
    os.makedirs(MNT_SYS_RO, exist_ok=True)
    os.makedirs(MNT_SYS_RW, exist_ok=True)
    subprocess.run(["umount", "-f", MNT_SYS_RO], stderr=subprocess.DEVNULL)
    subprocess.run(["umount", "-f", MNT_SYS_RW], stderr=subprocess.DEVNULL)
    
    if not os.path.exists(RAW_SYS_RO):
        print("  -> Unsparsing source system.img...")
        run_cmd([SIMG2IMG, os.path.join(BASE_DIR, "system.img"), RAW_SYS_RO])
        
    run_cmd(["mount", "-o", "loop,ro", RAW_SYS_RO, MNT_SYS_RO])
    
    print(f"  -> Creating fresh writable raw system ext4 image ({SYS_EXACT_SIZE:,} bytes)...")
    if os.path.exists(RAW_SYS_RW):
        os.remove(RAW_SYS_RW)
    run_cmd(["truncate", "-s", str(SYS_EXACT_SIZE), RAW_SYS_RW])
    run_cmd(["mkfs.ext4", "-F", "-L", "system", "-b", "4096", "-I", "256", RAW_SYS_RW])
    run_cmd(["mount", "-o", "loop,rw", RAW_SYS_RW, MNT_SYS_RW])
    
    try:
        print("  -> Copying files from base system to writable image (preserving attributes)...")
        run_cmd(["cp", "-a", f"{MNT_SYS_RO}/.", MNT_SYS_RW])
        
        sys_root = MNT_SYS_RW
        if os.path.exists(os.path.join(MNT_SYS_RW, "system")):
            sys_internal = os.path.join(MNT_SYS_RW, "system")
        else:
            sys_internal = MNT_SYS_RW

        # 1. phh-on-boot.sh
        phh_src = os.path.join(FIXES_DIR, "system/bin/phh-on-boot.sh")
        phh_dst = os.path.join(sys_internal, "bin/phh-on-boot.sh")
        shutil.copy2(phh_src, phh_dst)
        os.chmod(phh_dst, 0o755)
        print(f"  [+] Injected phh-on-boot.sh with 5G SA props, CarrierConfig and tethering")

        # 2. tethering_daemon.sh
        teth_src = os.path.join(FIXES_DIR, "system/bin/tethering_daemon.sh")
        teth_dst = os.path.join(sys_internal, "bin/tethering_daemon.sh")
        shutil.copy2(teth_src, teth_dst)
        os.chmod(teth_dst, 0o755)
        print(f"  [+] Injected tethering_daemon.sh")

        # 3. apns-conf.xml
        apns_sys_src = os.path.join(FIXES_DIR, "system/etc/apns-conf.xml")
        apns_sys_dst = os.path.join(sys_internal, "etc/apns-conf.xml")
        shutil.copy2(apns_sys_src, apns_sys_dst)
        os.chmod(apns_sys_dst, 0o644)
        print(f"  [+] Injected 5G NR apns-conf.xml into system/etc")

        # 4. Settings.apk with showNrList() patched
        settings_src = os.path.join(FIXES_DIR, "system/system_ext/priv-app/Settings/Settings.apk")
        possible_settings = [
            os.path.join(MNT_SYS_RW, "system_ext/priv-app/Settings/Settings.apk"),
            os.path.join(sys_internal, "system_ext/priv-app/Settings/Settings.apk"),
            os.path.join(sys_internal, "priv-app/Settings/Settings.apk")
        ]
        for p in possible_settings:
            if os.path.exists(p):
                shutil.copy2(settings_src, p)
                os.chmod(p, 0o644)
                oat_d = os.path.join(os.path.dirname(p), "oat")
                if os.path.exists(oat_d):
                    shutil.rmtree(oat_d, ignore_errors=True)
                print(f"  [+] Injected patched Settings.apk into {p}")
                break

        # 5. NetworkModeSwitcher.apk
        nms_src = os.path.join(FIXES_DIR, "system/app/NetworkModeSwitcher/NetworkModeSwitcher.apk")
        nms_dir = os.path.join(sys_internal, "app/NetworkModeSwitcher")
        os.makedirs(nms_dir, exist_ok=True)
        nms_dst = os.path.join(nms_dir, "NetworkModeSwitcher.apk")
        shutil.copy2(nms_src, nms_dst)
        os.chmod(nms_dst, 0o644)
        print(f"  [+] Injected NetworkModeSwitcher.apk (Galaxy 5G Tools)")

    finally:
        print("  -> Syncing and unmounting system images...")
        run_cmd(["sync"])
        run_cmd(["umount", MNT_SYS_RW])
        run_cmd(["umount", MNT_SYS_RO])

    print("  -> Converting to sparse system.img...")
    run_cmd([IMG2SIMG, RAW_SYS_RW, os.path.join(BASE_DIR, "system.img")])
    print(f"  [+] system.img successfully updated! ({os.path.getsize(os.path.join(BASE_DIR, 'system.img')):,} bytes)")

def rebuild_super_and_zip():
    print("\n==================================================")
    print("  [4/4] Assembling super.img & TWRP Flashable ZIP ")
    print("==================================================")
    # Assemble super.img
    super_script = os.path.join(TOOLS_DIR, "assemble_aosp_super.py")
    run_cmd(["python3", super_script])

    # Build TWRP Flashable ZIP
    zip_script = os.path.join(TOOLS_DIR, "create_aosp_twrp_zip.py")
    run_cmd(["python3", zip_script])

if __name__ == "__main__":
    update_vendor()
    update_product()
    update_system()
    rebuild_super_and_zip()
    print("\n==================================================")
    print("  ALL FIXES APPLIED & FLASHABLE ZIP REBUILT!      ")
    print("==================================================")
