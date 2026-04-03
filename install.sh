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
# Stop the service gracefully
svc -d "$SYMLINK"

# Wait until service stops or timeout
elapsed=0
while [ -e "$SYMLINK/supervise/ok" ] && [ $elapsed -lt 5 ]; do
    sleep 0.5
    elapsed=$((elapsed + 1))
done

# If still running, forcibly kill the process
if [ -e "$SYMLINK/supervise/ok" ]; then
    echo "Service did not stop gracefully, killing..."
    # Find the PID supervised by runit
    PID=$(cat "$SYMLINK/supervise/pid" 2>/dev/null)
    if [ -n "$PID" ]; then
        kill -9 "$PID" 2>/dev/null || true
    fi
fi

# Start the service
svc -u "$SYMLINK"
echo "Service restarted successfully."