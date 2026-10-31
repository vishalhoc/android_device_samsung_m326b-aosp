with open("I:/AOSP_Project/debug_logs/pmsg-ramoops-latest", "rb") as f:
    data = f.read().decode("latin1", errors="ignore")

lines = [l for l in data.splitlines() if any(c.isalnum() for c in l)]
print(f"Total lines in pmsg: {len(lines)}")
for l in lines[-60:]:
    print(l)
