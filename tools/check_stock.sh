#!/system/bin/sh
echo "=== 1. CRYPTO & STORAGE PROPERTIES ==="
getprop | grep -iE 'crypto|vold|fbe|knox|teegris|hardware|fstab'

echo "=== 2. METADATA & EFS PERMISSIONS & FILES ==="
ls -la /metadata
ls -la /metadata/vold 2>/dev/null
ls -la /efs 2>/dev/null
ls -la /mnt/vendor/efs 2>/dev/null

echo "=== 3. RUNNING MODULES & DETAILS ==="
cat /proc/modules

echo "=== 4. LOADED CONNECTIVITY SERVICES & FIRMWARE ==="
getprop | grep -iE 'wmt|wifi|wlan|bluetooth|bt|driver'
ps -ef | grep -iE 'wmt|wifi|bluetooth|wpa|conn|launcher|loader'
ls -la /vendor/firmware/ | grep -iE "soc2|wmt|wifi|bt"

echo "=== 5. TOUCHSCREEN FORENSICS ==="
ls -la /sys/class/sec/tsp/
cat /sys/class/sec/tsp/cmd_result 2>/dev/null
cat /sys/class/sec/tsp/cmd_list 2>/dev/null
dmesg | grep -iE "tsp|touch|ilitek|ili9881|sec_ts" | tail -n 30

echo "=== 6. AUDIO & SENSORS & DISPLAY HAL SERVICES ==="
ps -ef | grep -iE "audio|sensor|camera|display|composer|hwcomposer|light|power"

echo "=== 7. ACTIVE INIT SERVICES ==="
getprop | grep init.svc
