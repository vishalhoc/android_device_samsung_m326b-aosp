#
# Copyright (C) 2026 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/samsung/m326b

# Architecture
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-2a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_ABI2 :=
TARGET_CPU_VARIANT := cortex-a76

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv7-a-neon
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := cortex-a55

# Board Platform & Hardware
TARGET_BOARD_PLATFORM := mt6853
TARGET_BOOTLOADER_BOARD_NAME := k6853v1_64_titan
TARGET_NO_BOOTLOADER := true
TARGET_NO_RADIOIMAGE := true
BOARD_USES_MTK_HARDWARE := true
TARGET_USES_64_BIT_BINDER := true

# Display
TARGET_SCREEN_DENSITY := 300

# Target assertions
TARGET_OTA_ASSERT_DEVICE := m326b,SM-M326B,a32x

# Boot Image Header Version 2 Parameters
# Forensically extracted from SM-M326B stock boot.img
BOARD_BOOT_HEADER_VERSION := 2
BOARD_KERNEL_PAGESIZE := 2048
BOARD_KERNEL_BASE := 0x40000000
BOARD_KERNEL_OFFSET := 0x00080000
BOARD_RAMDISK_OFFSET := 0x07c80000
BOARD_TAGS_OFFSET := 0x0bc80000

BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)
BOARD_MKBOOTIMG_ARGS += --ramdisk_offset $(BOARD_RAMDISK_OFFSET)
BOARD_MKBOOTIMG_ARGS += --tags_offset $(BOARD_TAGS_OFFSET)
BOARD_MKBOOTIMG_ARGS += --board SRPTF26A012

# Kernel Cmdline
# Forensically extracted from live device /proc/cmdline
BOARD_KERNEL_CMDLINE := bootopt=64S3,32N2,64N2 loop.max_part=7

# Kernel Configuration
BOARD_KERNEL_IMAGE_NAME := Image.gz
TARGET_KERNEL_ARCH := arm64
TARGET_KERNEL_HEADER_ARCH := arm64
TARGET_KERNEL_CONFIG := a32x_defconfig
TARGET_KERNEL_SOURCE := kernel/samsung/m326b

# Physical Partition Sizing (Bytes)
BOARD_BOOTIMAGE_PARTITION_SIZE := 33554432
BOARD_DTBOIMG_PARTITION_SIZE := 8388608
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 41943040
BOARD_CACHEIMAGE_PARTITION_SIZE := 209715200

# Dynamic Partitions (Super Partition = 7,864,320,000 bytes)
BOARD_SUPER_PARTITION_SIZE := 7864320000
BOARD_SUPER_PARTITION_GROUPS := main
BOARD_MAIN_SIZE := 7860125696
BOARD_MAIN_PARTITION_LIST := system vendor product odm

# Filesystem Types
BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_PRODUCTIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_ODMIMAGE_FILE_SYSTEM_TYPE := ext4

TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true
BOARD_USES_METADATA_PARTITION := true

TARGET_COPY_OUT_VENDOR := vendor
TARGET_COPY_OUT_PRODUCT := product
TARGET_COPY_OUT_ODM := odm

# AVB (Android Verified Boot - Stock vbmeta flags: 0x3 = disabled verification & verity)
BOARD_AVB_ENABLE := true
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --flags 3

# Recovery
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/rootdir/etc/fstab.mt6853
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888

# VINTF Manifests
DEVICE_MANIFEST_FILE += $(DEVICE_PATH)/vintf/manifest.xml
DEVICE_MATRIX_FILE += $(DEVICE_PATH)/vintf/compatibility_matrix.xml

# SELinux
BOARD_VENDOR_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/vendor

# Kernel Modules (9 stock platform modules in /vendor/lib/modules/)
BOARD_VENDOR_KERNEL_MODULES += \
    $(DEVICE_PATH)/prebuilt/modules/bt_drv_connac1x.ko \
    $(DEVICE_PATH)/prebuilt/modules/wmt_drv.ko \
    $(DEVICE_PATH)/prebuilt/modules/connfem.ko \
    $(DEVICE_PATH)/prebuilt/modules/fmradio_drv_mt6631_6635.ko \
    $(DEVICE_PATH)/prebuilt/modules/gps_drv.ko \
    $(DEVICE_PATH)/prebuilt/modules/wmt_chrdev_wifi.ko \
    $(DEVICE_PATH)/prebuilt/modules/wlan_drv_gen4m.ko \
    $(DEVICE_PATH)/prebuilt/modules/fpsgo.ko \
    $(DEVICE_PATH)/prebuilt/modules/met.ko

# Include proprietary vendor BoardConfig if present
-include vendor/samsung/m326b/BoardConfigVendor.mk
