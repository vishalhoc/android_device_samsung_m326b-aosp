with open("I:/AOSP_Project/debug_logs/console-ramoops-latest", "rb") as f:
    data = f.read().decode("latin1", errors="ignore")

lines = data.splitlines()
print(f"Total lines: {len(lines)}")
for j in range(max(0, len(lines)-120), len(lines)):
    print(lines[j])
