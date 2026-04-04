#!/bin/sh

set -e

echo "Install BatteryCurrentRestrictor service..."

cd /data/battery-current-restrictor

chmod +x battery_current_restrictor.py
chmod +x service/run

# register service
SERVICE_NAME="battery-current-restrictor"
SYMLINK="/service/$SERVICE_NAME"
TARGET_BASE="/data/battery-current-restrictor"
TARGET="$TARGET_BASE/service"

# Create or update the symlink
ln -sf "$TARGET" "$SYMLINK"
echo "Symlink ensured: $SYMLINK -> $TARGET"

# Command to run on boot
RC_COMMAND="ln -sf $TARGET $SYMLINK"

# Ensure rc.local exists and is executable
if [ ! -f /data/rc.local ]; then
    echo -e "#!/bin/sh -e\n\nexit 0" > /etc/rc.local
    chmod +x /etc/rc.local
fi

# Add command to rc.local if not already present
if ! grep -Fxq "$TARGET_BASE/install.sh" /data/rc.local; then
    echo "$TARGET_BASE/install.sh" >> /data/rc.local
    echo "Added battery_current_restrictor to rc.local"
else
    echo "battery_current_restrictor already in rc.local"
fi

echo "Installation finished"

sleep 2

echo "(Re)starting service..."
pkill -f "$TARGET_BASE/battery_current_restrictor.py" 2>/dev/null || true

# Start the service
svc -u "$SYMLINK"
echo "Service restarted successfully."