#!/usr/bin/with-contenv bashio

# Konfiguration aus Home Assistant Addon-Config lesen
export FRITZ_HOST=$(bashio::config 'fritz_host')
export FRITZ_PASS=$(bashio::config 'fritz_pass')
export FRITZ_USER=$(bashio::config 'fritz_user')
export REFRESH_RATE=$(bashio::config 'refresh_rate')

bashio::log.info "Starte Fritz!Box Mesh Overview..."
bashio::log.info "Fritz!Box Host: ${FRITZ_HOST}"

# Python-App starten
python3 /app/main.py
