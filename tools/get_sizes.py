import struct, os

def get_unsparsed_size(path):
    with open(path, "rb") as f:
        magic = struct.unpack("<I", f.read(4))[0]
        if magic == 0xED26FF3A:
            f.seek(0)
            hdr = f.read(28)
            magic, major, minor, file_hdr_sz, chunk_hdr_sz, blk_sz, total_blks, total_chunks, img_checksum = struct.unpack("<I4H4I", hdr)
            return blk_sz * total_blks
        else:
            return os.path.getsize(path)

for img in ["aosp-arm64-ab-vanilla-13.0-20230919.img", "vendor.img", "product.img", "odm.img"]:
    p = os.path.join("/mnt/i/AOSP_Project", img)
    sz = get_unsparsed_size(p)
    print(f"{img}: unsparsed={sz:,} bytes ({sz} bytes)")
