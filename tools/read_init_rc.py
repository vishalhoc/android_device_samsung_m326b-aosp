with open("/build/lineage20/out/target/product/m326b/recovery/root/system/etc/init/hw/init.rc", "r") as f:
    text = f.read()

for l in text.splitlines():
    if any(k in l.lower() for k in ["adbd", "usb", "configfs", "musb", "gadget"]):
        print(l)
