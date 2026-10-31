import os
import zipfile
import shutil

BASE_DIR = "I:/AOSP_Project"
FIXES_DIR = os.path.join(BASE_DIR, "collected_fixes")
OUT_ZIP = os.path.join(BASE_DIR, "AOSP-13-M326B-All-Fixes-Flashable.zip")

print("==========================================================")
print("  Building Standalone Universal Fixes Flashable ZIP       ")
print("==========================================================")

# Update binary script supporting TWRP recovery and Magisk
UPDATE_BINARY = """#!/sbin/sh
# Universal Fixes Flashable Installer for Samsung Galaxy M32 5G (SM-M326B)
# Supports TWRP Recovery & Direct Partition Injection

OUTFD=$2
ZIPFILE=$3

ui_print() {
    if [ -n "$OUTFD" ] && [ -e "/proc/self/fd/$OUTFD" ]; then
        echo "ui_print $1" >"/proc/self/fd/$OUTFD"
        echo "ui_print" >"/proc/self/fd/$OUTFD"
    else
        echo "$1"
    fi
}

ui_print "=================================================="
ui_print "  AOSP 13 All-Fixes Universal Flashable Package   "
ui_print "  Target: Samsung Galaxy M32 5G (SM-M326B)        "
ui_print "=================================================="

# Detect environment: Magisk or TWRP
if [ -n "$BOOTMODE" ] || [ -f "/data/adb/magisk/util_functions.sh" ]; then
    ui_print "[*] Running in Magisk environment..."
    # Magisk handles extraction to $MODPATH
    exit 0
fi

ui_print "[*] Running in Recovery (TWRP) mode..."
TMP_DIR="/tmp/m326b_fixes"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

ui_print "[*] Extracting fix files..."
unzip -o "$ZIPFILE" "system/*" "vendor/*" -d "$TMP_DIR" >/dev/null 2>&1

# Mount dynamic partitions
ui_print "[*] Mounting system, vendor, and product..."
mount -o rw /system_root 2>/dev/null || mount -o rw /system 2>/dev/null
mount -o rw /vendor 2>/dev/null
mount -o rw /product 2>/dev/null

SYS_MNT="/system_root"
[ ! -d "$SYS_MNT/system" ] && [ -d "/system" ] && SYS_MNT="/system"

if [ -d "$SYS_MNT" ]; then
    ui_print "[+] Installing System updates (5G SA scripts, tethering, Settings, APNs)..."
    cp -af "$TMP_DIR/system/bin/phh-on-boot.sh" "$SYS_MNT/system/bin/phh-on-boot.sh" 2>/dev/null || cp -af "$TMP_DIR/system/bin/phh-on-boot.sh" "$SYS_MNT/bin/phh-on-boot.sh"
    chmod 755 "$SYS_MNT/system/bin/phh-on-boot.sh" 2>/dev/null || chmod 755 "$SYS_MNT/bin/phh-on-boot.sh"

    cp -af "$TMP_DIR/system/bin/tethering_daemon.sh" "$SYS_MNT/system/bin/tethering_daemon.sh" 2>/dev/null || cp -af "$TMP_DIR/system/bin/tethering_daemon.sh" "$SYS_MNT/bin/tethering_daemon.sh"
    chmod 755 "$SYS_MNT/system/bin/tethering_daemon.sh" 2>/dev/null || chmod 755 "$SYS_MNT/bin/tethering_daemon.sh"

    cp -af "$TMP_DIR/system/etc/apns-conf.xml" "$SYS_MNT/system/etc/apns-conf.xml" 2>/dev/null || cp -af "$TMP_DIR/system/etc/apns-conf.xml" "$SYS_MNT/etc/apns-conf.xml"
    chmod 644 "$SYS_MNT/system/etc/apns-conf.xml" 2>/dev/null || chmod 644 "$SYS_MNT/etc/apns-conf.xml"

    # Settings.apk
    if [ -f "$SYS_MNT/system/system_ext/priv-app/Settings/Settings.apk" ]; then
        cp -af "$TMP_DIR/system/system_ext/priv-app/Settings/Settings.apk" "$SYS_MNT/system/system_ext/priv-app/Settings/Settings.apk"
        rm -rf "$SYS_MNT/system/system_ext/priv-app/Settings/oat"
    fi

    # NetworkModeSwitcher
    mkdir -p "$SYS_MNT/system/app/NetworkModeSwitcher"
    cp -af "$TMP_DIR/system/app/NetworkModeSwitcher/NetworkModeSwitcher.apk" "$SYS_MNT/system/app/NetworkModeSwitcher/NetworkModeSwitcher.apk"
    chmod 644 "$SYS_MNT/system/app/NetworkModeSwitcher/NetworkModeSwitcher.apk"
fi

if [ -d "/product" ]; then
    ui_print "[+] Installing Product updates (5GHz WiFi overlay & APNs)..."
    mkdir -p /product/overlay
    cp -af "$TMP_DIR/system/product/overlay/wifi-5g-overlay.apk" "/product/overlay/wifi-5g-overlay.apk"
    chmod 644 "/product/overlay/wifi-5g-overlay.apk"

    cp -af "$TMP_DIR/system/product/etc/apns-conf.xml" "/product/etc/apns-conf.xml"
    chmod 644 "/product/etc/apns-conf.xml"
fi

if [ -d "/vendor" ]; then
    ui_print "[+] Installing Vendor updates (5G SA libsec-ril, 5GHz hostapd, light-service, modules)..."
    cp -af "$TMP_DIR/vendor/lib64/libsec-ril.so" "/vendor/lib64/libsec-ril.so"
    chmod 644 "/vendor/lib64/libsec-ril.so"

    cp -af "$TMP_DIR/vendor/bin/hw/hostapd" "/vendor/bin/hw/hostapd"
    chmod 755 "/vendor/bin/hw/hostapd"

    cp -af "$TMP_DIR/vendor/bin/hw/vendor.samsung.hardware.light-service" "/vendor/bin/hw/vendor.samsung.hardware.light-service"
    chmod 755 "/vendor/bin/hw/vendor.samsung.hardware.light-service"

    cp -af "$TMP_DIR/vendor/etc/vintf/manifest.xml" "/vendor/etc/vintf/manifest.xml"
    chmod 644 "/vendor/etc/vintf/manifest.xml"

    cp -af "$TMP_DIR/vendor/etc/init/init.adb.early.rc" "/vendor/etc/init/init.adb.early.rc"
    chmod 644 "/vendor/etc/init/init.adb.early.rc"

    cp -af "$TMP_DIR/vendor/etc/init/boot_watchdog.rc" "/vendor/etc/init/boot_watchdog.rc"
    chmod 644 "/vendor/etc/init/boot_watchdog.rc"

    cp -af "$TMP_DIR/vendor/bin/boot_watchdog.sh" "/vendor/bin/boot_watchdog.sh"
    chmod 755 "/vendor/bin/boot_watchdog.sh"

    if [ -f "$TMP_DIR/vendor/lib/modules/wlan_drv_gen4m.ko" ]; then
        cp -af "$TMP_DIR/vendor/lib/modules/wlan_drv_gen4m.ko" "/vendor/lib/modules/wlan_drv_gen4m.ko"
        chmod 644 "/vendor/lib/modules/wlan_drv_gen4m.ko"
    fi
fi

ui_print "[*] Syncing filesystems..."
sync
umount /product 2>/dev/null
umount /vendor 2>/dev/null
umount /system_root 2>/dev/null || umount /system 2>/dev/null

rm -rf "$TMP_DIR"
ui_print "=================================================="
ui_print "  All Fixes Successfully Flashed & Applied!       "
ui_print "=================================================="
exit 0
"""

UPDATER_SCRIPT = "# Dummy updater-script for Edify compatibility\n"

# Magisk module properties
MODULE_PROP = """id=m326b_aosp_all_fixes
name=Galaxy M32 5G (SM-M326B) AOSP All-In-One Fixes
version=v2.0-Production
versionCode=20
author=DeepMind Antigravity
description=Complete hardware, 5G SA telephony, dual-band 5GHz WiFi, USB tethering, and display HAL fixes for Galaxy M32 5G running AOSP 13.
"""

CUSTOMIZE_SH = """#!/system/bin/sh
ui_print "**************************************************"
ui_print "  Installing Galaxy M32 5G AOSP All-In-One Fixes  "
ui_print "**************************************************"

# Extract module files
ui_print "- Extracting module files..."
unzip -o "$ZIPFILE" 'system/*' -d $MODPATH >&2

# Set permissions
set_perm_recursive $MODPATH 0 0 0755 0644
set_perm $MODPATH/system/bin/phh-on-boot.sh 0 0 0755
set_perm $MODPATH/system/bin/tethering_daemon.sh 0 0 0755

ui_print "- Injected 5G SA telephony, 5GHz WiFi overlay, and tethering daemon!"
"""

def build_standalone_zip():
    if os.path.exists(OUT_ZIP):
        os.remove(OUT_ZIP)
        
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as z:
        # Installer files
        z.writestr("META-INF/com/google/android/update-binary", UPDATE_BINARY)
        z.writestr("META-INF/com/google/android/updater-script", UPDATER_SCRIPT)
        
        # Magisk files
        z.writestr("module.prop", MODULE_PROP)
        z.writestr("customize.sh", CUSTOMIZE_SH)
        
        # Walk and add all files from collected_fixes
        for root, dirs, files in os.walk(FIXES_DIR):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, FIXES_DIR).replace("\\", "/")
                z.write(abs_path, rel_path)
                print(f"  -> Added {rel_path} ({os.path.getsize(abs_path):,} bytes)")

    sz = os.path.getsize(OUT_ZIP)
    print(f"\n[+] SUCCESS: Created {OUT_ZIP} ({sz:,} bytes / {sz/(1024*1024):.2f} MB)")

if __name__ == "__main__":
    build_standalone_zip()
