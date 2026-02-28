#!/bin/bash

# Define paths
SCRIPT_DIR="/home/$USER"
PYTHON_SCRIPT="$SCRIPT_DIR/udpclient.py"
SERVICE_FILE="$HOME/.config/systemd/user/screen-state.service"

# Stop and disable the service
echo "Stopping and disabling the screen-state service..."
systemctl --user stop screen-state.service 2>/dev/null
systemctl --user disable screen-state.service 2>/dev/null

# Reload systemd to reflect changes
echo "Reloading systemd daemon..."
systemctl --user daemon-reload

# Remove the Python script
echo "Removing Python script: $PYTHON_SCRIPT..."
rm -f "$PYTHON_SCRIPT"

# Remove the service file
echo "Removing service file: $SERVICE_FILE..."
rm -f "$SERVICE_FILE"

# Optional: Clean up logs (uncomment if desired)
 #echo "Cleaning up logs..."
 #journalctl --user --vacuum-time=1s

echo "Cleanup complete! Verifying service is gone..."
systemctl --user status screen-state.service 2>/dev/null || echo "Service successfully removed."