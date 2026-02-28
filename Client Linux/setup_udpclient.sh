#!/bin/bash

# Define paths
SCRIPT_DIR="/home/$USER"
PYTHON_SCRIPT="$SCRIPT_DIR/udpclient.py"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/screen-state.service"

# Ensure the systemd user directory exists
echo "Creating systemd user directory if it doesn't exist..."
mkdir -p "$SERVICE_DIR"

# Install netifaces module
echo "Installing netifaces module..."
pip3 install netifaces

# Write the Python script
echo "Writing Python script to $PYTHON_SCRIPT..."
cat > "$PYTHON_SCRIPT" << 'EOF'
#!/usr/bin/env python3
import socket
import time
import json
import subprocess
import os
import netifaces

# Server configuration
SERVER_IP = "10.20.10.1"
SERVER_PORT = 12345

# Create UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Get the MAC address of the WiFi interface
def get_mac_address():
    try:
        # Get all network interfaces
        interfaces = netifaces.interfaces()
        # Common WiFi interface name patterns
        wifi_prefixes = ['wlan', 'wlp', 'wifi']
        
        # Look for a WiFi interface
        for iface in interfaces:
            if any(iface.startswith(prefix) for prefix in wifi_prefixes):
                # Get addresses for this interface
                addrs = netifaces.ifaddresses(iface)
                # Check for MAC address (AF_LINK)
                if netifaces.AF_LINK in addrs:
                    mac = addrs[netifaces.AF_LINK][0]['addr']
                    return mac
        return "Unknown (no WiFi interface found)"
    except Exception as e:
        return f"Unknown (error: {str(e)})"

# Get screen state using loginctl
def get_screen_state():
    try:
        uid = str(os.getuid())
        result = subprocess.run(['loginctl', 'list-sessions'], capture_output=True, text=True, timeout=2)
        sessions = result.stdout.splitlines()
        
        session_id = None
        for line in sessions:
            fields = line.split()
            if len(fields) >= 6 and fields[1] == uid and fields[4] == "user":
                session_id = fields[0]
                break
        
        if not session_id:
            for line in sessions:
                fields = line.split()
                if len(fields) >= 2 and fields[1] == uid:
                    session_id = fields[0]
                    break
        
        if not session_id:
            return "Unknown (no active session found for UID {})".format(uid)

        result = subprocess.run(
            ['loginctl', 'show-session', session_id, '-p', 'Active', '-p', 'LockedHint'],
            capture_output=True, text=True, timeout=2
        )
        output = result.stdout.strip().split('\n')
        if len(output) < 2:
            return "Unknown (unexpected loginctl output for session {})".format(session_id)
        
        active = "yes" in output[0].lower()
        locked = "yes" in output[1].lower()

        if not active:
            return "Off"
        elif locked:
            return "Locked"
        else:
            return "On"
    except FileNotFoundError:
        return "Unknown (loginctl not installed)"
    except subprocess.TimeoutExpired:
        return "Unknown (loginctl timed out)"
    except Exception as e:
        return f"Unknown (error: {str(e)})"

# Main loop
mac_address = get_mac_address()
print(f"Starting UDP client with MAC: {mac_address}")

# Send interval in seconds
SEND_INTERVAL = 30

# Last send time
last_send_time = time.time() - SEND_INTERVAL  # Send immediately on start

while True:
    try:
        current_time = time.time()
        
        # Check if 30 seconds have passed since the last send
        if current_time - last_send_time >= SEND_INTERVAL:
            # Get current screen state
            current_state = get_screen_state()
            
            # Prepare and send state
            state = {
                "mac_address": mac_address,
                "screen_state": current_state,
            }
            message = json.dumps(state).encode('utf-8')
            client_socket.sendto(message, (SERVER_IP, SERVER_PORT))
            print(f"Sent to {SERVER_IP}:{SERVER_PORT}: {state}")
            
            # Update last send time
            last_send_time = current_time
        
        # Small sleep to avoid excessive CPU usage
        time.sleep(0.5)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)  # Longer sleep on error before retrying
EOF

# Make the Python script executable
echo "Making Python script executable..."
chmod +x "$PYTHON_SCRIPT"

# Write the systemd service file
echo "Writing systemd service file to $SERVICE_FILE..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Screen State UDP Client
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 -u $PYTHON_SCRIPT
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

# Reload systemd, enable, and start the service
echo "Setting up the service..."
systemctl --user daemon-reload
systemctl --user enable screen-state.service
systemctl --user start screen-state.service

# Check the status
echo "Checking service status..."
systemctl --user status screen-state.service

echo "Setup complete! Check logs with: journalctl --user -u screen-state.service -f"
