#!/system/bin/sh
# Galaxy M32 5G Touchscreen & Backlight Initializer for AOSP Android 13
# Prevents touch freezing, black screen, and uninitialized IRAM firmware

# 1. Wake LCD Backlight immediately
echo 150 > /sys/class/leds/lcd-backlight/brightness 2>/dev/null
echo 150 > /sys/devices/platform/panel/panel_drv/backlight/panel/brightness 2>/dev/null

# 2. Reload Ilitek TDDI Firmware into IRAM
cat /sys/class/sec/tsp/cmd_result >/dev/null 2>&1
echo fw_update > /sys/class/sec/tsp/cmd 2>/dev/null
sleep 1.5
echo 1 > /sys/class/sec/tsp/enabled 2>/dev/null

# 3. Grant full rw permissions on sysfs nodes
chmod 0666 /sys/class/sec/tsp/* 2>/dev/null
chmod 0666 /sys/class/leds/lcd-backlight/brightness 2>/dev/null
chmod 0666 /sys/devices/platform/panel/panel_drv/backlight/panel/brightness 2>/dev/null
