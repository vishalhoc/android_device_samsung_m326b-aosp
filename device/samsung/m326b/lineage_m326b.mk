#
# Copyright (C) 2026 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from those products by default
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit from m326b device configuration
$(call inherit-product, device/samsung/m326b/device.mk)

# Inherit some common Lineage stuff
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)

# Product metadata
PRODUCT_NAME := lineage_m326b
PRODUCT_DEVICE := m326b
PRODUCT_MANUFACTURER := samsung
PRODUCT_BRAND := samsung
PRODUCT_MODEL := SM-M326B

PRODUCT_GMS_CLIENTID_BASE := android-samsung

# Build fingerprint and overrides from live device forensic dump
PRODUCT_BUILD_PROP_OVERRIDES += \
    PRODUCT_NAME=a32xins \
    PRODUCT_DEVICE=a32x \
    TARGET_DEVICE=a32x

BUILD_FINGERPRINT := samsung/a32xins/a32x:13/TP1A.220624.014/M326BDDSCCYD1:user/release-keys
PRODUCT_PROPERTY_OVERRIDES += \
    ro.build.fingerprint=$(BUILD_FINGERPRINT)
