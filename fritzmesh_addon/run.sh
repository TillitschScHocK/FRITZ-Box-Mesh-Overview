#!/usr/bin/with-contenv bashio

set -e

# Virtualenv aktivieren
source /opt/venv/bin/activate

# Home Assistant Addon Config auslesen
FRITZ_HOST=$(bashio::config 'fritz_host')
FRITZ_PASS=$(bashio::config 'fritz_pass')
FRITZ_USER=$(bashio::config 'fritz_user')
REFRESH_RATE=$(bashio::config 'refresh_rate')

# Umgebungsvariablen exportieren
export FRITZ_HOST
export FRITZ_PASS
export FRITZ_USER
export REFRESH_RATE

bashio::log.info "========================================="
bashio::log.info "Fritz!Box Mesh Overview v2.1"
bashio::log.info "========================================="
bashio::log.info "Host: ${FRITZ_HOST}"
bashio::log.info "Benutzer: ${FRITZ_USER}"
bashio::log.info "Refresh: ${REFRESH_RATE}s"
bashio::log.info "Starte Python-Anwendung..."
bashio::log.info "========================================="

# Python-App starten
exec python3 /app/main.py
