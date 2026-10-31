import os, tarfile, hashlib

dir_path = "I:/AOSP_Project"
tar_path = os.path.join(dir_path, "AP_M326B_AOSP13.tar")
tar_md5_path = os.path.join(dir_path, "AP_M326B_AOSP13.tar.md5")

images = [
    ("boot.img", os.path.join(dir_path, "kernel/boot.img")),
    ("recovery.img", os.path.join(dir_path, "recovery/recovery.img")),
    ("super.img", os.path.join(dir_path, "super.img")),
    ("vbmeta.img", "I:/LineageOS_Project/device_vbmeta.img"),
]

print("==========================================================")
print("  Assembling Samsung Galaxy M32 5G Odin AP Package")
print("==========================================================")

with tarfile.open(tar_path, "w") as tar:
    for arcname, srcpath in images:
        sz = os.path.getsize(srcpath)
        print(f"Adding {arcname} ({sz:,} bytes)...")
        tar.add(srcpath, arcname=arcname)

print("Calculating MD5 checksum...")
md5 = hashlib.md5()
with open(tar_path, "rb") as f:
    while chunk := f.read(1024 * 1024 * 4):
        md5.update(chunk)

md5_hex = md5.hexdigest()
print(f"MD5: {md5_hex}")

# Standard Odin trailer: "\n<md5_hex>  <filename>\n"
with open(tar_path, "ab") as f:
    f.write(f"\n{md5_hex}  AP_M326B_AOSP13.tar\n".encode("ascii"))

if os.path.exists(tar_md5_path):
    os.remove(tar_md5_path)
os.rename(tar_path, tar_md5_path)
final_sz = os.path.getsize(tar_md5_path)
print(f"SUCCESS: AP_M326B_AOSP13.tar.md5 created ({final_sz:,} bytes / {final_sz / (1024*1024*1024):.2f} GB)!")
