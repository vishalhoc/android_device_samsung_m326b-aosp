import subprocess

def run_debugfs(cmd, img):
    res = subprocess.run(["debugfs", "-R", cmd, img], capture_output=True, text=True)
    return res.stdout

print("=== Checking vendor_working.img for /bin/hw ===")
out = run_debugfs("ls -l /bin/hw", "/build/vendor_working.img")
for l in out.splitlines():
    if any(k in l.lower() for k in ["key", "gate", "crypto", "tz", "sec"]):
        print("VEN HW:", l)
