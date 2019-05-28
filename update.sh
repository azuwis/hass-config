#!/bin/sh
download() {
    file="$1"
    url="$2"
    echo "Downloading $file"
    curl --create-dirs -sfSLo "$file" "$url"
}

download_multi() {
    file_base="$1"
    shift
    url_base="$1"
    shift
    for file in "$@"
    do
        download "${file_base}/${file}" "${url_base}/${file}"
    done
}

download_multi custom_components/smartir https://github.com/smartHomeHub/SmartIR/raw/master/smartir __init__.py climate.py controller.py manifest.json services.yaml
download custom_components/smartir/codes/climate/1180.json https://github.com/smartHomeHub/SmartIR/raw/master/codes/climate/1180.json

download_multi custom_components/xiaomi_miio_airconditioningcompanion https://github.com/syssi/xiaomi_airconditioningcompanion/raw/develop/custom_components/xiaomi_miio_airconditioningcompanion __init__.py climate.py manifest.json
patch -p1 -i patches/smartir.diff

download custom_components/braviatv_psk/media_player.py https://github.com/custom-components/media_player.braviatv_psk/raw/master/custom_components/braviatv_psk/media_player.py

download www/slider-entity-row.js https://github.com/thomasloven/lovelace-slider-entity-row/raw/master/slider-entity-row.js

download themes/midnight.yaml https://github.com/maartenpaauw/home-assistant-community-themes/raw/master/midnight.yaml
echo '  sidebar-icon-color: "#D0D0D0"' >> themes/midnight.yaml

mini_media_player="$(curl --silent https://api.github.com/repos/kalkih/mini-media-player/releases/latest | awk -F'"' '/browser_download_url/ {print $4}')"
download www/mini-media-player.js "$mini_media_player"

simple_thermostat="$(curl --silent https://api.github.com/repos/nervetattoo/simple-thermostat/releases/latest | awk -F'"' '/browser_download_url/ {print $4}')"
download www/simple-thermostat.js "$simple_thermostat"

download custom_components/aligenie.py https://github.com/feversky/aligenie/raw/master/aligenie.py
