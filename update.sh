#!/bin/sh
download() {
    file="$1"
    url="$2"
    echo "Downloading $file"
    curl --create-dirs -#fSLo "$file" "$url"
}


download broadlink_climate_codes/gree.ini https://github.com/vpnmaster/homeassistant-custom-components/raw/master/broadlink_climate_codes/gree.ini
download custom_components/climate/broadlink.py https://github.com/vpnmaster/homeassistant-custom-components/raw/master/custom_components/climate/broadlink.py
download custom_components/climate/xiaomi_miio.py https://github.com/syssi/xiaomi_airconditioningcompanion/raw/develop/custom_components/climate/xiaomi_miio.py
download custom_components/media_player/braviatv_psk.py https://github.com/gerard33/home-assistant/raw/master/braviatv_psk.py
download www/mini-media-player.js https://github.com/kalkih/mini-media-player/releases/download/v0.9.0/mini-media-player-bundle.js
download www/slider-entity-row.js https://github.com/thomasloven/lovelace-slider-entity-row/raw/master/slider-entity-row.js

download themes/midnight.yaml https://github.com/maartenpaauw/home-assistant-community-themes/raw/master/midnight.yaml
echo '  sidebar-icon-color: "#D0D0D0"' >> themes/midnight.yaml
