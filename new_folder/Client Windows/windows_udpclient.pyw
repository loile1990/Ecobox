#!/usr/bin/env python3
import socket
import subprocess
import time
import json
import win32gui
import win32api
import os
import logging
import sys
import re

# Server configuration
SERVER_IP = "10.20.10.1"
SERVER_PORT = 12345

# Script configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "screen_monitor.log")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create UDP socket
def create_socket():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5.0)
        return sock
    except Exception as e:
        logging.error(f"Failed to create socket: {e}")
        sys.exit(1)

client_socket = create_socket()

# Get the MAC address
def get_mac_address():
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW  # Suppress CMD window
        )
        output = result.stdout
        mac_address = None
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("Physical address"):
                match = re.search(r"Physical address\s*:\s*([\da-fA-F:]{17})", line)
                if match:
                    mac_address = match.group(1).lower()
                    break
        if not mac_address:
            logging.error("No MAC address found for Wi-Fi interface")
            return "Unknown"
        return mac_address
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running netsh command: {e}")
        return "Unknown"
    except Exception as e:
        logging.error(f"Error getting MAC address: {e}")
        return "Unknown"

# Get screen state on Windows
def get_screen_state():
    try:
        # Check if workstation is locked
        if win32gui.GetForegroundWindow() == 0:
            return "Locked"
        return "On"
    except Exception as e:
        logging.error(f"Error getting screen state: {e}")
        return "On"  # Default to On if error occurs

# Main loop
def main():
    logging.info(f"Script started with PID: {os.getpid()}")

    SEND_INTERVAL = 30.0
    last_send_time = time.time() - SEND_INTERVAL

    while True:
        try:
            current_time = time.time()
            if current_time - last_send_time >= SEND_INTERVAL:
                # Fetch MAC address fresh each time
                mac_address = get_mac_address()
                current_state = get_screen_state()
                state = {
                    "mac_address": mac_address,
                    "screen_state": current_state
                }
                message = json.dumps(state).encode('utf-8')
                client_socket.sendto(message, (SERVER_IP, SERVER_PORT))
                logging.info(f"Sent to {SERVER_IP}:{SERVER_PORT}: {state}")
                last_send_time = current_time
            time.sleep(0.5)
        except socket.timeout:
            logging.warning("Socket timeout, retrying...")
        except Exception as e:
            logging.error(f"Script error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Script terminated by user")
        client_socket.close()
        sys.exit(0)
