#!/bin/sh

set -e

echo "Install BatteryCurrentRestrictor service..."

cd /data/battery-current-restrictor

chmod +x battery_current_restrictor.py
chmod +x service/run

# register service
SERVICE_NAME="battery-current-restrictor"

ln -sf /data/battery-current-restrictor/service /service/$SERVICE_NAME

echo "Installation finished"

sleep 2

echo "(Re)starting service..."
svc -t /service/$SERVICE_NAME 2>/dev/null || svc -u /service/$SERVICE_NAME || true