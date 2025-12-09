#!/usr/bin/with-contenv bashio

# Config-Werte lesen
FRITZ_HOST=$(bashio::config 'fritz_host')
FRITZ_PASS=$(bashio::config 'fritz_pass')
FRITZ_USER=$(bashio::config 'fritz_user')
REFRESH_RATE=$(bashio::config 'refresh_rate')

# Als Umgebungsvariablen exportieren
export FRITZ_HOST
export FRITZ_PASS
export FRITZ_USER
export REFRESH_RATE

bashio::log.info "Starte Fritz!Box Mesh Overview..."
bashio::log.info "Fritz!Box Host: ${FRITZ_HOST}"

# Python-App starten
exec python3 /app/main.py
