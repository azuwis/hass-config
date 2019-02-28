#!/bin/sh
download() {
    file="$1"
    url="$2"
    echo "Downloading $file"
    curl --create-dirs -sfSLo "$file" "$url"
}


download broadlink_climate_codes/gree.ini https://github.com/vpnmaster/homeassistant-custom-components/raw/master/broadlink_climate_codes/gree.ini
download custom_components/climate/broadlink.py https://github.com/vpnmaster/homeassistant-custom-components/raw/master/custom_components/climate/broadlink.py
download custom_components/xiaomi_miio/climate.py https://github.com/syssi/xiaomi_airconditioningcompanion/raw/develop/custom_components/xiaomi_miio/climate.py
download custom_components/xiaomi_miio/__init__.py https://github.com/syssi/xiaomi_airconditioningcompanion/raw/develop/custom_components/xiaomi_miio/__init__.py
download custom_components/media_player/braviatv_psk.py https://github.com/gerard33/home-assistant/raw/master/braviatv_psk.py
download www/slider-entity-row.js https://github.com/thomasloven/lovelace-slider-entity-row/raw/master/slider-entity-row.js

download themes/midnight.yaml https://github.com/maartenpaauw/home-assistant-community-themes/raw/master/midnight.yaml
echo '  sidebar-icon-color: "#D0D0D0"' >> themes/midnight.yaml

mini_media_player="$(curl --silent https://api.github.com/repos/kalkih/mini-media-player/releases/latest | awk -F'"' '/browser_download_url/ {print $4}')"
download www/mini-media-player.js "$mini_media_player"
