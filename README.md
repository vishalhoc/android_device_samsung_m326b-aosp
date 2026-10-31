# AOSP 13 Device Tree & Production Build Suite — Samsung Galaxy M32 5G (SM-M326B)

[![AOSP](https://img.shields.io/badge/AOSP-Android%2013-3DDC84.svg?logo=android)](https://source.android.com)
[![Device](https://img.shields.io/badge/Device-Samsung%20Galaxy%20M32%205G%20(SM--M326B)-034EA2.svg)](https://www.samsung.com)
[![Platform](https://img.shields.io/badge/Platform-MediaTek%20MT6853%20Dimensity%20720-FF6600.svg)](https://www.mediatek.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Complete pure AOSP 13 (Tiramisu) device configuration, proprietary HAL patchsuite, kernel modules, dynamic partition assembly pipeline, and universal flashable installer tools for **Samsung Galaxy M32 5G (SM-M326B / a32xins)**.

---

## Device Specifications

| Feature | Specification |
|:---|:---|
| **Marketing Name** | Samsung Galaxy M32 5G |
| **Model Number** | `SM-M326B` (India / INS, Binary C) |
| **Device Codename** | `m326b` / `a32x` (`a32xins`) |
| **SoC** | MediaTek MT6853 Dimensity 720 5G (7nm) |
| **CPU** | Octa-core (2x 2.0 GHz Cortex-A76 & 6x 2.0 GHz Cortex-A55) |
| **GPU** | ARM Mali-G57 MC3 |
| **Display** | 6.5" TFT LCD, 720 x 1600 px (Ilitek TDDI ILI9881X / ILI7806S) |
| **Memory / Storage** | 6/8 GB LPDDR4X / 128 GB UFS 2.1 |
| **5G Bands** | Sub-6: n1, n3, n5, n7, n8, n20, n28, n38, n40, n41, n77, n78 (SA/NSA) |
| **Kernel Version** | Linux 4.14.186 (OSS MediaTek 4.14 base) |
| **Base Android** | Android 13 (One UI 5.1 firmware baseline `M326BDDSCCYD1`) |

---

## Key Hardware & Framework Implementations

### 1. 5G Standalone (SA) Telephony & Data Stack
* **Samsung RIL SA Unlock:** Reverse-engineered and patched `/vendor/lib64/libsec-ril.so` (`SupportSaModel`, `isSupportSaModel`, `IsSupportSaEpdgHandover` -> returns 1), enabling native 5G SA registration on Indian carriers (Reliance Jio True 5G).
* **Telephony APN Bitmask Fix:** Replaced legacy LTE-only bitmasks (`network_type_bitmask="13"`) with dual-stack NR definitions (`network_type_bitmask="13|20"`) across `/system/etc/apns-conf.xml` and `/product/etc/apns-conf.xml`. This eliminates the Android 13 `DataNetworkController` `NO_SUITABLE_DATA_PROFILE` connection block on 5G SA.
* **Preferred Network Type Dialog:** Patched `Settings.apk` (`showNrList()` in `classes.dex`) to unconditionally present **5G (recommended)**, **4G**, **3G**, and **2G**.
* **CarrierConfig Status Bar Overrides:** Automated boot injection of `always_show_data_rat_icon_bool=true`, `hide_lte_plus_data_icon_bool=false`, `show_4g_for_lte_data_icon_bool=true`, and 5G icon rules (`connected:5G,not_restricted_rrc_con:5G`), ensuring clear 5G/4G badges appear alongside the signal bar.

### 2. Wi-Fi & Hotspot Dual-Band 5GHz
* **SoftAP 5GHz Channel Unlock:** Patched vendor `hostapd` binary to bypass restrictive country-code and DFS channel assertions, enabling 5GHz Wi-Fi tethering.
* **RRO Overlay:** Injected `wifi-5g-overlay.apk` (`config_wifi_dual_band_support=true`, `config_wifi_softap_ieee80211ac_supported=true`, `config_wifi_fast_bss_transition_enabled=true`).
* **Kernel Wi-Fi Driver:** Includes source-patched MediaTek Gen4m module (`wlan_drv_gen4m.ko`) with DBDC concurrent interface support.

### 3. USB Peripheral & Tethering Subsystem
* **MediaTek PHY Gadget Initialization:** `init.adb.early.rc` forces `musb-hdrc` into full peripheral mode (`cmode 3`), disabling power-saving disconnects and mapping Samsung USB IDs (`0x04E8` / `0x6860`) for MTP, ADB, File Transfer, and MIDI.
* **USB Tethering Forwarding Daemon:** Background service (`tethering_daemon.sh`) monitoring `rndis0`/`ncm0`/`usb0` to auto-configure upstream NAT forwarding via `iptables` and rule routing.

### 4. Display, Touch & HAL Stability
* **Ilitek TDDI Touch Keepalive:** Custom touch initializer (`tsp_init.sh` and IDC config `sec_touchscreen.idc`) preventing sleep-mode touch detachment.
* **Light Service Crash Fix:** Patched `vendor.samsung.hardware.light-service` preventing `sec-light-hal-2-0` restart loops.
* **Autonomous Boot Watchdog:** 180s fail-safe service (`boot_watchdog.sh`) auto-rebooting to TWRP if the system encounters a framework deadlock.

---

## Repository Tree Structure

```text
├── device/samsung/m326b/          # AOSP Device Tree
│   ├── Android.bp                 # Build blueprint
│   ├── Android.mk                 # Device makefile
│   ├── AndroidProducts.mk         # Product lunch definitions (aosp_m326b)
│   ├── BoardConfig.mk             # Board architecture, partitions, and kernel parameters
│   ├── device.mk                  # Hardware module and copy rule inclusions
│   ├── aosp_m326b.mk              # AOSP ROM target configuration
│   ├── configs/                   # Audio, media, seccomp, and Wi-Fi configurations
│   ├── overlay/                   # RRO framework overlays
│   ├── rootdir/                   # Root init scripts (init.m326b.rc, fstab.emmc)
│   └── vintf/                     # Validated VINTF HAL manifest
├── tools/                         # Automated ROM & Image Assembly Suite
│   ├── apply_all_fixes_and_rebuild.py # Automated end-to-end patch and repack pipeline
│   ├── assemble_aosp_super.py     # lpmake dynamic super.img compilation script
│   ├── create_aosp_twrp_zip.py    # Zero-temp streaming TWRP flashable ZIP builder
│   ├── create_standalone_fixes_zip.py # Dual-mode TWRP & Magisk update ZIP builder
│   ├── lpmake                     # AOSP logical partition maker tool
│   ├── simg2img                   # Sparse image unsparse utility
│   └── img2simg                   # Raw image sparse utility
├── installer_tools/               # Device flashing binaries
│   ├── sparse_flash               # Direct-to-block streaming sparse flasher
│   └── simg2img                   # ARM64 recovery tool
├── META-INF/                      # TWRP Universal Installer scripts
│   └── com/google/android/
│       ├── update-binary          # Dual loopback & sparse_flash recovery installer
│       └── updater-script        # Edify compatibility bridge
├── collected_fixes/               # Extracted and verified production binaries & configs
│   ├── system/                    # Patched Settings.apk, APN XMLs, phh-on-boot.sh, daemon
│   └── vendor/                    # 5G SA libsec-ril.so, hostapd, light-service, watchdog
├── touch_fix/                     # Ilitek TDDI touchscreen IDC & service files
├── modules/                       # MediaTek MT6853 source-compiled kernel modules
├── manifest.xml                   # HAL compatibility matrix
└── init.adb.early.rc              # Boot-level root ADB & MTP initialization
```

---

## Build Instructions

### Prerequisites
- Linux / WSL (Ubuntu 20.04 or 22.04 LTS recommended)
- Python 3.8+
- Android build dependencies: `e2fsprogs`, `libsparse`, `zip`, `unzip`

### Compiling `super.img` & Full Flashable ZIP
1. Place base unsparsed partitions (`system.img`, `vendor.img`, `product.img`, `odm.img`) into the workspace directory.
2. Run the automated patch & assembly pipeline:
   ```bash
   python3 tools/apply_all_fixes_and_rebuild.py
   ```
3. The script will automatically:
   - Mount and inject all fixes into `vendor`, `product`, and `system`.
   - Re-sparse the images.
   - Run `lpmake` to generate `super.img` (7.86 GB dynamic capacity).
   - Package `AOSP-13-UNOFFICIAL-m326b-TWRP.zip` with verified byte offsets.

### Building Standalone Update Package
To build the lightweight, in-place update ZIP (flashes over any existing AOSP GSI without wiping userdata):
```bash
python3 tools/create_standalone_fixes_zip.py
```
Output: `AOSP-13-M326B-All-Fixes-Flashable.zip` (26 MB).

---

## Installation via TWRP Recovery

1. Boot device into TWRP Recovery.
2. **If clean installing AOSP 13:**
   - Transfer `AOSP-13-UNOFFICIAL-m326b-TWRP.zip` to your MicroSD card or via `adb push`.
   - In TWRP: **Install** -> Select `AOSP-13-UNOFFICIAL-m326b-TWRP.zip` -> **Swipe to Flash**.
   - After flashing finishes: **Wipe** -> **Format Data** -> type `yes` (removes Knox encryption).
   - Reboot System.
3. **If updating an existing AOSP / GSI installation:**
   - Flash `AOSP-13-M326B-All-Fixes-Flashable.zip` directly in TWRP (or install via the Magisk app).
   - Reboot System.

---

## Credits & License

- **Developer:** Vishal ([@vishalhoc](https://github.com/vishalhoc))
- **AOSP / Project Treble:** Google, Pierre-Hervé Tual (Phh-Treble)
- **TWRP Team:** TeamWin Recovery Project
- **License:** Licensed under the [Apache License, Version 2.0](LICENSE).
