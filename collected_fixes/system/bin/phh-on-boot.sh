#!/system/bin/sh

vndk="$(getprop persist.sys.vndk)"
[ -z "$vndk" ] && vndk="$(getprop ro.vndk.version |grep -oE '^[0-9]+')"

[ "$(getprop vold.decrypt)" = "trigger_restart_min_framework" ] && exit 0

setprop ctl.start media.swcodec

for i in wpa p2p;do
	if [ ! -f /data/misc/wifi/${i}_supplicant.conf ];then
		cp /vendor/etc/wifi/wpa_supplicant.conf /data/misc/wifi/${i}_supplicant.conf
	fi
	chmod 0660 /data/misc/wifi/${i}_supplicant.conf
	chown wifi:system /data/misc/wifi/${i}_supplicant.conf
done

if [ -f /system/bin/hostapd_patched ]; then
    mount -o bind /system/bin/hostapd_patched /vendor/bin/hw/hostapd
fi

if [ -f /vendor/bin/mtkmal ];then
    if [ "$(getprop persist.mtk_ims_support)" = 1 ] || [ "$(getprop persist.mtk_epdg_support)" = 1 ];then
        setprop persist.mtk_ims_support 0
        setprop persist.mtk_epdg_support 0
        reboot
    fi
fi

if grep -qF android.hardware.boot /vendor/manifest.xml || grep -qF android.hardware.boot /vendor/etc/vintf/manifest.xml ;then
	bootctl mark-boot-successful
fi

setprop ctl.restart sec-light-hal-2-0
if find /sys/firmware -name support_fod |grep -qE .;then
	setprop ctl.restart vendor.fps_hal
fi

setprop ctl.stop storageproxyd

sleep 10

minijailSrc=/system/system_ext/apex/com.android.vndk.v28/lib/libminijail.so
minijailSrc64=/system/system_ext/apex/com.android.vndk.v28/lib64/libminijail.so
if [ "$vndk" = 27 ];then
    mount $minijailSrc64 /vendor/lib64/libminijail_vendor.so
    mount $minijailSrc /vendor/lib/libminijail_vendor.so
fi

if [ "$vndk" = 28 ];then
    mount $minijailSrc64 /vendor/lib64/libminijail_vendor.so
    mount $minijailSrc /vendor/lib/libminijail_vendor.so
    mount $minijailSrc64 /system/lib64/vndk-28/libminijail.so
    mount $minijailSrc /system/lib/vndk-28/libminijail.so
    mount $minijailSrc64 /vendor/lib64/libminijail.so
    mount $minijailSrc /vendor/lib/libminijail.so
fi

#Clear looping services
sleep 30
getprop | \
    grep restarting | \
    sed -nE -e 's/\[([^]]*).*/\1/g'  -e 's/init.svc.(.*)/\1/p' |
    while read -r svc ;do
        setprop ctl.stop "$svc"
    done

# 5G SA and Telephony enhancements
setprop ril.supportSA 1
setprop persist.ril.supportNrModefromCp 1
setprop persist.vendor.radio.nr_sa_support 1
setprop persist.radio.is_vonr_enabled_0 true

# Telephony APN fix for 5G NR
sqlite3 /data/user_de/0/com.android.providers.telephony/databases/telephony.db "UPDATE carriers SET bearer=0, bearer_bitmask=0, network_type_bitmask=0 WHERE apn='jionet';"

# Carrier configs
cmd phone cc set-value -p prefer_2g_bool true
cmd phone cc set-value -p show_4g_for_lte_data_icon_bool true
cmd phone cc set-value -p show_4glte_for_lte_data_icon_bool true
cmd phone cc set-value -p carrier_nr_availabilities_int_array 1 2
cmd phone cc set-value -p 5g_icon_configuration_string "connected_mmwave:5G_PLUS,connected:5G,not_restricted_rrc_idle:5G,not_restricted_rrc_con:5G"
cmd phone cc set-value -p carrier_wfc_ims_available_bool true
cmd phone cc set-value -p carrier_default_wfc_ims_enabled_bool true
cmd phone cc set-value -p world_mode_enabled_bool false

/system/bin/tethering_daemon.sh &
# RAT icon and status bar display enhancements
cmd phone cc set-value -s 0 -p always_show_data_rat_icon_bool true
cmd phone cc set-value -s 0 -p hide_lte_plus_data_icon_bool false
cmd phone cc set-value -s 0 -p show_ims_registration_status_bool true
cmd phone cc set-value -s 0 -p show_wifi_calling_icon_in_status_bar_bool true
sqlite3 /data/user_de/0/com.android.providers.telephony/databases/telephony.db "UPDATE carriers SET bearer=0, bearer_bitmask=0, network_type_bitmask=0;"
