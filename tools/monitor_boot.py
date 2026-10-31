import subprocess
import time
import sys

ADB = r"C:\Users\visha\AppData\Local\Android\Sdk\platform-tools\adb.exe"

print("==========================================================", flush=True)
print("  AOSP 13 Boot & Watchdog Monitor Started", flush=True)
print("==========================================================", flush=True)

start_time = time.time()
while time.time() - start_time < 200:
    elapsed = int(time.time() - start_time)
    try:
        out = subprocess.run([ADB, "devices"], capture_output=True, text=True, timeout=5).stdout
    except Exception as e:
        time.sleep(3)
        continue
    
    lines = [line.strip() for line in out.strip().splitlines() if line.strip() and not line.startswith("*")]
    devices = [l for l in lines if not l.startswith("List")]
    
    if devices:
        print(f"[{elapsed}s] Detected devices: {devices}", flush=True)
        for dev in devices:
            if "\tdevice" in dev:
                print(f"[!] Device connected in SYSTEM mode at {elapsed}s!", flush=True)
                try:
                    res = subprocess.run([ADB, "shell", "getprop sys.boot_completed"], capture_output=True, text=True, timeout=5).stdout.strip()
                    print(f"    sys.boot_completed = '{res}'", flush=True)
                    init_svc = subprocess.run([ADB, "shell", "getprop init.svc.bootanim"], capture_output=True, text=True, timeout=5).stdout.strip()
                    print(f"    init.svc.bootanim = '{init_svc}'", flush=True)
                    model = subprocess.run([ADB, "shell", "getprop ro.product.model"], capture_output=True, text=True, timeout=5).stdout.strip()
                    print(f"    ro.product.model = '{model}'", flush=True)
                except Exception as ex:
                    print(f"    Error reading props: {ex}", flush=True)
            elif "\trecovery" in dev:
                print(f"[!] Device connected in RECOVERY mode at {elapsed}s!", flush=True)
                try:
                    last_kmsg = subprocess.run([ADB, "shell", "cat /sys/fs/pstore/console-ramoops-0 2>/dev/null || cat /sys/fs/pstore/console-ramoops 2>/dev/null"], capture_output=True, text=True, timeout=5).stdout
                    if last_kmsg:
                        print("--- RAMOOPS TAIL ---", flush=True)
                        for line in last_kmsg.splitlines()[-25:]:
                            print(f"    {line}", flush=True)
                except Exception as ex:
                    pass
    else:
        if elapsed % 10 == 0:
            print(f"[{elapsed}s] Waiting for device / recovery connection...", flush=True)
            
    time.sleep(3)

print("Monitor finished.", flush=True)
