import os
import re
import sys
import zipfile

if os.path.exists("/mnt/i/AOSP_Project"):
    dir_path = "/mnt/i/AOSP_Project"
else:
    dir_path = "I:/AOSP_Project"
final_zip_path = os.path.join(dir_path, "AOSP-13-UNOFFICIAL-m326b-TWRP.zip")
tmp_zip_path = os.path.join(dir_path, "tmp_aosp_install.zip")

print("==========================================================")
print("  Building AOSP 13 TWRP Flashable ZIP for Galaxy M32 5G")
print("==========================================================")

# Files to bundle
ub_path = os.path.join(dir_path, "META-INF", "com", "google", "android", "update-binary")
us_path = os.path.join(dir_path, "META-INF", "com", "google", "android", "updater-script")
sparse_flash_path = os.path.join(dir_path, "installer_tools", "sparse_flash")
simg2img_path = os.path.join(dir_path, "installer_tools", "simg2img")
vbmeta_path = os.path.join(dir_path, "vbmeta.img")
boot_path = os.path.join(dir_path, "kernel", "boot.img")
recovery_path = os.path.join(dir_path, "recovery", "recovery.img")
super_path = os.path.join(dir_path, "super.img")

for p in [ub_path, us_path, sparse_flash_path, simg2img_path, vbmeta_path, boot_path, recovery_path, super_path]:
    if not os.path.exists(p):
        print(f"[-] ERROR: Required file missing: {p}")
        sys.exit(1)
    sz = os.path.getsize(p)
    print(f"  [+] Found: {os.path.basename(p)} ({sz:,} bytes)")

super_size = os.path.getsize(super_path)
print(f"\n[*] super.img size: {super_size:,} bytes")

with open(us_path, "rb") as f:
    us_data = f.read()

with open(sparse_flash_path, "rb") as f:
    sparse_flash_data = f.read()

with open(simg2img_path, "rb") as f:
    simg2img_data = f.read()

with open(vbmeta_path, "rb") as f:
    vbmeta_data = f.read()

with open(boot_path, "rb") as f:
    boot_data = f.read()

with open(recovery_path, "rb") as f:
    recovery_data = f.read()

with open(ub_path, "r", encoding="utf-8") as f:
    ub_text = f.read()

def build_zip(ub_content_bytes, target_path):
    with zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_STORED) as zout:
        zout.writestr("META-INF/com/google/android/update-binary", ub_content_bytes)
        zout.writestr("META-INF/com/google/android/updater-script", us_data)
        zout.writestr("tools/sparse_flash", sparse_flash_data)
        zout.writestr("tools/simg2img", simg2img_data)
        zout.writestr("vbmeta.img", vbmeta_data)
        zout.writestr("boot.img", boot_data)
        zout.writestr("recovery.img", recovery_data)
        
        hdr_offset = zout.fp.tell()
        print("  -> Streaming super.img into ZIP package...")
        zout.write(super_path, "super.img")
    
    with zipfile.ZipFile(target_path, "r") as zcheck:
        info = zcheck.getinfo("super.img")
        data_offset = info.header_offset + 30 + len(info.filename) + len(info.extra)
    return hdr_offset, data_offset

# Pass 1: measure offset
print("\n[*] Pass 1: Measuring super.img offset in package...")
hdr_offset, data_offset = build_zip(ub_text.encode("utf-8"), tmp_zip_path)
print(f"  [i] Pass 1 super.img data offset: {data_offset:,}")

# Update offsets in update-binary with exact 12-digit zero-padding
offset_str = f"{data_offset:012d}"
size_str = f"{super_size:012d}"
ub_text_updated = re.sub(r'SUPER_OFFSET_RAW=\d+', f'SUPER_OFFSET_RAW={offset_str}', ub_text)
ub_text_updated = re.sub(r'SUPER_SIZE_RAW=\d+', f'SUPER_SIZE_RAW={size_str}', ub_text_updated)

assert len(ub_text_updated) == len(ub_text), "update-binary byte length must not change"

with open(ub_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(ub_text_updated)

# Pass 2: build final with exact baked offsets
print("\n[*] Pass 2: Rebuilding final ZIP with baked offset metadata...")
hdr_offset2, data_offset2 = build_zip(ub_text_updated.encode("utf-8"), tmp_zip_path)
print(f"  [i] Pass 2 super.img data offset: {data_offset2:,}")
assert data_offset2 == data_offset, f"Offset shifted! {data_offset2} != {data_offset}"

# Verify sparse magic directly at data_offset
print("\n[*] Verifying sparse header at computed offset...")
with open(tmp_zip_path, "rb") as f:
    f.seek(data_offset)
    magic = f.read(4)
    if magic != b"\x3a\xff\x26\xed":
        print(f"[-] ERROR: Bad magic at offset {data_offset}: {magic.hex()}")
        sys.exit(1)
    print(f"  [+] SUCCESS: Verified sparse magic 0xED26FF3A at offset {data_offset}!")

# Replace destination zip
if os.path.exists(final_zip_path):
    os.remove(final_zip_path)
os.rename(tmp_zip_path, final_zip_path)

final_sz = os.path.getsize(final_zip_path)
print(f"\n==========================================================")
print(f"  SUCCESS: {os.path.basename(final_zip_path)} created!")
print(f"  File size: {final_sz:,} bytes ({final_sz / (1024*1024*1024):.2f} GB)")
print(f"==========================================================")
