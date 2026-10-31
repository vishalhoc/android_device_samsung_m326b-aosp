import xml.etree.ElementTree as ET

manifest_file = r"I:\AOSP_Project\manifest.xml"

with open(manifest_file, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Expand graphics.composer to include 2.1, 2.2, 2.3
old_composer = """    <hal format="hidl">
        <name>android.hardware.graphics.composer</name>
        <transport>hwbinder</transport>
        <version>2.1</version>
        <interface>
            <name>IComposer</name>
            <instance>default</instance>
        </interface>
        <fqname>@2.1::IComposer/default</fqname>
    </hal>"""

new_composer = """    <hal format="hidl">
        <name>android.hardware.graphics.composer</name>
        <transport>hwbinder</transport>
        <version>2.1</version>
        <version>2.2</version>
        <version>2.3</version>
        <interface>
            <name>IComposer</name>
            <instance>default</instance>
        </interface>
        <fqname>@2.1::IComposer/default</fqname>
        <fqname>@2.2::IComposer/default</fqname>
        <fqname>@2.3::IComposer/default</fqname>
    </hal>"""

text = text.replace(old_composer, new_composer)

# 2. Add DRM, Health, Thermal, Wifi, and Fingerprint before </manifest>
additional_hals = """
    <hal format="hidl">
        <name>android.hardware.drm</name>
        <transport>hwbinder</transport>
        <version>1.4</version>
        <interface>
            <name>ICryptoFactory</name>
            <instance>clearkey</instance>
            <instance>widevine</instance>
        </interface>
        <interface>
            <name>IDrmFactory</name>
            <instance>clearkey</instance>
            <instance>widevine</instance>
        </interface>
        <fqname>@1.4::ICryptoFactory/clearkey</fqname>
        <fqname>@1.4::IDrmFactory/clearkey</fqname>
        <fqname>@1.4::ICryptoFactory/widevine</fqname>
        <fqname>@1.4::IDrmFactory/widevine</fqname>
    </hal>
    <hal format="hidl">
        <name>android.hardware.health</name>
        <transport>hwbinder</transport>
        <version>2.1</version>
        <interface>
            <name>IHealth</name>
            <instance>default</instance>
        </interface>
        <fqname>@2.1::IHealth/default</fqname>
    </hal>
    <hal format="hidl">
        <name>vendor.samsung.hardware.thermal</name>
        <transport>hwbinder</transport>
        <version>1.0</version>
        <interface>
            <name>ISehThermal</name>
            <instance>default</instance>
        </interface>
        <fqname>@1.0::ISehThermal/default</fqname>
    </hal>
    <hal format="hidl">
        <name>vendor.samsung.hardware.wifi</name>
        <transport>hwbinder</transport>
        <version>2.3</version>
        <interface>
            <name>ISehWifi</name>
            <instance>default</instance>
        </interface>
        <fqname>@2.3::ISehWifi/default</fqname>
    </hal>
    <hal format="hidl">
        <name>vendor.samsung.hardware.biometrics.fingerprint</name>
        <transport>hwbinder</transport>
        <version>3.0</version>
        <interface>
            <name>ISehBiometricsFingerprint</name>
            <instance>default</instance>
        </interface>
        <fqname>@3.0::ISehBiometricsFingerprint/default</fqname>
    </hal>
</manifest>"""

text = text.replace("</manifest>", additional_hals)

with open(manifest_file, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)

print(f"Patched {manifest_file} successfully! New size: {len(text)} bytes")
