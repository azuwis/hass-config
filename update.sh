#!/bin/sh
download() {
    file="$1"
    url="$2"
    echo "Downloading $file"
    curl --create-dirs -#fSLo "$file" "$url"
}


download custom_components/media_player/braviatv_psk.py https://github.com/gerard33/home-assistant/raw/master/braviatv_psk.py
download custom_components/climate/xiaomi_miio.py https://github.com/syssi/xiaomi_airconditioningcompanion/raw/develop/custom_components/climate/xiaomi_miio.py
download broadlink_climate_codes/gree.ini https://github.com/vpnmaster/homeassistant-custom-components/raw/master/broadlink_climate_codes/gree.ini
download custom_components/climate/broadlink.py https://github.com/vpnmaster/homeassistant-custom-components/raw/master/custom_components/climate/broadlink.py
