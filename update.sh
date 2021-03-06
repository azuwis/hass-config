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

download_multi custom_components/smartir https://github.com/smartHomeHub/SmartIR/raw/master/custom_components/smartir __init__.py climate.py controller.py fan.py manifest.json media_player.py services.yaml
# download custom_components/smartir/codes/climate/1180.json https://github.com/smartHomeHub/SmartIR/raw/master/codes/climate/1180.json
mkdir -p a/custom_components b/custom_components
rsync -a --exclude '__pycache__/' --exclude '**.orig' --exclude '**.rej' custom_components/smartir a/custom_components/
patch -p1 -i patches/smartir.diff
rsync -a --exclude '__pycache__/' --exclude '**.orig' --exclude '**.rej' custom_components/smartir b/custom_components/
diff -Nur a b | filterdiff --remove-timestamps > patches/smartir.diff
#rm -r a b

download_multi custom_components/xiaomi_miio_airconditioningcompanion https://github.com/syssi/xiaomi_airconditioningcompanion/raw/develop/custom_components/xiaomi_miio_airconditioningcompanion __init__.py climate.py manifest.json services.yaml

download_multi custom_components/braviatv_psk https://github.com/custom-components/media_player.braviatv_psk/raw/master/custom_components/braviatv_psk __init__.py manifest.json media_player.py services.yaml

# download www/slider-entity-row.js https://github.com/thomasloven/lovelace-slider-entity-row/raw/master/slider-entity-row.js

download themes/midnight.yaml https://github.com/maartenpaauw/home-assistant-community-themes/raw/master/midnight.yaml
echo '  sidebar-icon-color: "#D0D0D0"' >> themes/midnight.yaml

mini_media_player="$(curl --silent https://api.github.com/repos/kalkih/mini-media-player/releases/latest | awk -F'"' '/browser_download_url/ {print $4}')"
download www/mini-media-player.js "$mini_media_player"

simple_thermostat="$(curl --silent https://api.github.com/repos/nervetattoo/simple-thermostat/releases/latest | awk -F'"' '/browser_download_url/ {print $4}')"
download www/simple-thermostat.js "$simple_thermostat"

download_multi custom_components/aligenie https://github.com/feversky/aligenie/raw/master/aligenie __init__.py
