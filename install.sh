#!/bin/sh

set -e

echo "Install BatteryCurrentRestrictor service..."

cd /data

# Clone / update
if [ ! -d "battery-current-restrictor" ]; then
    git clone https://github.com/schnitzel001/BatteryCurrentRestrictor.git battery-current-restrictor
else
    cd battery-current-restrictor
    git pull
fi

cd /data/battery-current-restrictor

pip3 install -r requirements.txt

chmod +x battery_current_restrictor.py
chmod +x service/run

# register service
SERVICE_NAME="battery-current-restrictor"

ln -sf /data/battery-current-restrictor/service /service/$SERVICE_NAME

echo "Installation finished"
echo "Starting service..."

svc -u /service/$SERVICE_NAME || true