#!/bin/sh

set -e

echo "Install BatteryCurrentRestrictor service..."

cd /data/battery-current-restrictor

chmod +x battery_current_restrictor.py
chmod +x service/run

# register service
SERVICE_NAME="battery-current-restrictor"
SYMLINK="/service/$SERVICE_NAME"
TARGET="/data/battery-current-restrictor/service"

# Create or update the symlink
ln -sf "$TARGET" "$SYMLINK"
echo "Symlink ensured: $SYMLINK -> $TARGET"

# Command to run on boot
RC_COMMAND="ln -sf $TARGET $SYMLINK"

# Ensure rc.local exists and is executable
if [ ! -f /etc/rc.local ]; then
    echo -e "#!/bin/sh -e\n\nexit 0" > /etc/rc.local
    chmod +x /etc/rc.local
fi

# Add command to rc.local if not already present
if ! grep -Fxq "$RC_COMMAND" /etc/rc.local; then
    sed -i "/^exit 0/i $RC_COMMAND" /etc/rc.local
    echo "Added symlink command to rc.local"
else
    echo "Symlink command already in rc.local"
fi

echo "Installation finished"

sleep 2

echo "(Re)starting service..."
#svc -t /service/$SERVICE_NAME 2>/dev/null || svc -u /service/$SERVICE_NAME || true
# Stop the service
if svc -d "$SYMLINK"; then
    echo "Stopping service..."
    # Wait until service is stopped
    while [ -e "$SYMLINK/supervise/ok" ]; do
        sleep 0.1
    done
fi

# Start the service
svc -u "$SYMLINK"
echo "Service restarted successfully."