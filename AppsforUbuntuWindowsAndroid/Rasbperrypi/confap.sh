#!/bin/bash

# Annule tout si erreur
set -ex
# Installation des paquets
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent
sudo apt install ifupdown hostapd dnsmasq conntrack python3 jq -y

# Arrêt des services si lancés
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

# Config de la static IP pour wlan0
sudo bash -c 'cat > /etc/network/interfaces' <<EOF
auto wlan0
iface wlan0 inet static
    address 10.20.10.1
    netmask 255.255.255.0
    network 10.20.10.0
    broadcast 10.20.10.255
EOF

# Configure dnsmasq
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.backup 2>/dev/null || true
sudo bash -c 'cat > /etc/dnsmasq.conf' <<EOF
interface=wlan0
dhcp-range=10.20.10.2,10.20.10.254,255.255.255.0,infinite
domain=local
address=/rt.local/10.20.10.1
EOF

# Config Hostapd
sudo bash -c 'cat > /etc/hostapd/hostapd.conf' <<EOF
interface=wlan0
driver=nl80211
ssid=ecobox
hw_mode=g
channel=0
wmm_enabled=1
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=ecobox123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
country_code=FR
ieee80211n=1
ieee80211ac=0
ctrl_interface=/var/run/hostapd
ctrl_interface_group=0
EOF

sudo sed -i 's|^#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

# Config NAT
if ! sudo iptables -t nat -C POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null; then
    sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
    sudo netfilter-persistent save
fi

# IPV4 forwarding
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.d/routed-ap.conf 2>/dev/null; then
    echo "net.ipv4.ip_forward=1" | sudo tee /etc/sysctl.d/routed-ap.conf
    sudo sysctl --system
fi

# Service nf_conntrack_acct
sudo bash -c 'cat > /etc/systemd/system/nf_conntrack_acct.service' <<EOF
[Unit]
Description=Enable nf_conntrack_acct
After=network.target
[Service]
Type=oneshot
ExecStart=/bin/sh -c "echo 1 > /proc/sys/net/netfilter/nf_conntrack_acct"
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable nf_conntrack_acct.service

# Activation des interfaces et services
sudo systemctl unmask hostapd
sudo systemctl enable hostapd dnsmasq
sudo nmcli connection down Wired\ connection\ 1 || true
sudo nmcli connection up Wired\ connection\ 1 || true
sudo nmcli device down eth0 || true
sudo nmcli device up eth0 || true
sudo ifdown wlan0 || true
sudo ifup wlan0 || true
sudo systemctl restart NetworkManager || true

sudo systemctl start hostapd dnsmasq nf_conntrack_acct.service

# Répertoire courant
CURRENT_DIR="${PWD}"
NAT_LOG_DIR="${CURRENT_DIR}/nat_logs"
mkdir -p "$NAT_LOG_DIR"

# Script UDP Server
UDP_SERVER_SCRIPT="${CURRENT_DIR}/udp_server.py"
sudo bash -c "cat > $UDP_SERVER_SCRIPT" <<EOF
#!/usr/bin/env python3
import socket
import json
import sys
import os
import re
import time

# Configuration
SERVER_IP = "10.20.10.1"
SERVER_PORT = 12345
STATE_FILE = "/tmp/udp_client_states.json"

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_IP, SERVER_PORT))

print(f"UDP server started on {SERVER_IP}:{SERVER_PORT}")

client_states = {}

def update_state_file():
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(client_states, f)
    except Exception as e:
        print(f"Error writing state file: {e}", file=sys.stderr)

def load_state_file():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                loaded_states = json.load(f)
                current_time = time.time()
                for mac, state in loaded_states.items():
                    state["last_update"] = state.get("last_update", current_time)
                return loaded_states
        except json.JSONDecodeError:
            print("Warning: State file corrupted, starting fresh", file=sys.stderr)
            return {}
    return {}

def process_json_message(data):
    print(f"Received raw data: {data!r}", file=sys.stderr)
    try:
        state = json.loads(data)
        if not all(key in state for key in ['mac_address', 'screen_state']):
            raise ValueError("Missing required fields")
        mac_address = state['mac_address']
        screen_state = state['screen_state']
        state_entry = {"mac_address": mac_address, "screen_state": screen_state, "last_update": time.time()}
        client_states[mac_address] = state_entry
        print(f"Updated state from PC {mac_address}: {screen_state}")
        return True
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error processing JSON message: {e}", file=sys.stderr)
        return False

def process_phone_message(data):
    print(f"Received raw data: {data!r}", file=sys.stderr)
    try:
        message = data.decode('utf-8')
        match = re.findall(r'\[(\w{2}(?::?\w{2}){5})]\s*(\w+)', message)
        if match and len(match[0]) == 2:
            mac_address, screen_state = match[0]
            state_entry = {"mac_address": mac_address, "screen_state": screen_state, "last_update": time.time()}
            client_states[mac_address] = state_entry
            print(f"Updated state from phone {mac_address}: {screen_state}")
            return True
        return False
    except (UnicodeDecodeError, ValueError) as e:
        print(f"Error processing phone message: {e}", file=sys.stderr)
        return False

client_states = load_state_file()

while True:
    try:
        server_socket.settimeout(1.0)
        try:
            data, addr = server_socket.recvfrom(1024)
        except socket.timeout:
            continue
        print(f"Received raw data from {addr[0]}: {data!r}", file=sys.stderr)
        if process_phone_message(data):
            update_state_file()
        elif process_json_message(data):
            update_state_file()
        else:
            print(f"Warning: Unrecognized message format from {addr[0]}", file=sys.stderr)
    except Exception as e:
        print(f"Error in main loop: {e}", file=sys.stderr)
        continue
EOF

sudo chmod +x "$UDP_SERVER_SCRIPT"

sudo bash -c "cat > /etc/systemd/system/udp-server.service" <<EOF
[Unit]
Description=UDP Server for MAC Address
After=network.target
[Service]
ExecStart=/usr/bin/env python3 $UDP_SERVER_SCRIPT
WorkingDirectory=$CURRENT_DIR
Restart=always
StandardOutput=journal
StandardError=journal
[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable udp-server.service
sudo systemctl start udp-server.service

# --- Création du script de capture NAT avec reprise du dernier numéro ---
NAT_CAPTURE_SCRIPT="${CURRENT_DIR}/capture.sh"
sudo bash -c "cat > $NAT_CAPTURE_SCRIPT" <<EOF
#!/bin/bash

# Fichier temporaire contenant les états UDP
STATE_FILE="/tmp/udp_client_states.json"

# Interface réseau filaire
WIRED_IFACE="eth0"
WIRED_CONN="Wired connection 1"

# Fonction pour réinitialiser l'interface filaire
reset_wired_interface() {
    echo "Réinitialisation de l'interface \$WIRED_IFACE..." >&2
    nmcli connection down "\$WIRED_CONN" >/dev/null 2>&1 || true
    nmcli connection up "\$WIRED_CONN" >/dev/null 2>&1 || true
    sudo nmcli device down "\$WIRED_IFACE" >/dev/null 2>&1 || true
    sudo nmcli device up "\$WIRED_IFACE" >/dev/null 2>&1 || true
}

# Fonction pour tester la connectivité Internet
test_connectivity() {
    echo "Test de la connectivité Internet..." >&2
    if ping -I "\$WIRED_IFACE" -c 4 8.8.8.8 >/dev/null 2>&1; then
        echo "Connectivité Internet confirmée." >&2
        return 0
    else
        echo "Aucune connectivité Internet détectée." >&2
        return 1
    fi
}

# Boucle pour réinitialiser l'interface et tester la connexion jusqu'à succès
while true; do
    reset_wired_interface
    sleep 10
    if test_connectivity; then
        break
    else
        echo "Échec de la connexion. Nouvelle tentative dans 10 secondes..." >&2
    fi
done

# Attendre 5 minutes avant de commencer la capture
sleep 600

# Préfixe des fichiers de sortie dans le répertoire courant
BASE_OUTPUT_FILE="$CURRENT_DIR/nat_logs/nat_logs"
EXTENSION=".txt"
INTERVAL=30

# Vérifie si conntrack est installé
if ! command -v conntrack &> /dev/null; then
    echo "Erreur : 'conntrack' n'est pas installé." >&2
    exit 1
fi

# Vérifie si iw est installé
if ! command -v iw &> /dev/null; then
    echo "Erreur : 'iw' n'est pas installé." >&2
    exit 1
fi

# Vérifie si jq est installé
if ! command -v jq &> /dev/null; then
    echo "Erreur : 'jq' n'est pas installé." >&2
    exit 1
fi

# Récupérer l'IP de l'interface eth0 (utilisée pour le NAT)
# Boucle pour attendre que l'IP soit disponible
for i in {1..10}; do
    ETH0_IP=\$(ip addr show eth0 | grep -oP '(?<=inet\s)\d+\.\d+\.\d+\.\d+' | head -1)
    if [ -n "\$ETH0_IP" ]; then
        break
    fi
    echo "IP de eth0 non trouvée, nouvelle tentative dans 10 secondes..." >&2
    sleep 10
done

# Vérifier si ETH0_IP a été récupérée
if [ -z "\$ETH0_IP" ]; then
    echo "Erreur : Impossible de récupérer l'IP de eth0 après plusieurs tentatives." >&2
    exit 1
fi

echo "IP de eth0 détectée : \$ETH0_IP" >&2

# Fonction pour vérifier si une IP est privée
is_private_ip() {
    local ip=\$1
    # Convertir l'IP en un tableau d'octets
    IFS='.' read -r -a octets <<< "\$ip"

    # Vérifier les plages d'IP privées
    if [ "\${octets[0]}" -eq 10 ]; then
        return 0  # 10.0.0.0/8
    elif [ "\${octets[0]}" -eq 172 ] && [ "\${octets[1]}" -ge 16 ] && [ "\${octets[1]}" -le 31 ]; then
        return 0  # 172.16.0.0/12
    elif [ "\${octets[0]}" -eq 192 ] && [ "\${octets[1]}" -eq 168 ]; then
        return 0  # 192.168.0.0/16
    elif [ "\${octets[0]}" -eq 127 ]; then
        return 0  # 127.0.0.0/8 (loopback)
    fi
    return 1  # IP publique
}

# Fonction pour anonymiser une IP publique en la remplaçant par une IP fictive
# Utilisation de la plage 203.0.113.x (réservée pour la documentation, RFC 5737)
anonymize_ip() {
    local ip=\$1
    # Débogage : afficher l'IP en cours de traitement
    echo "Vérification de l'IP : \$ip" >&2
    # Ne pas anonymiser si l'IP correspond à celle de eth0
    if [ "\$ip" = "\$ETH0_IP" ]; then
        echo "IP de eth0 détectée, aucune anonymisation : \$ip" >&2
        echo "\$ip"
        return
    fi
    if is_private_ip "\$ip"; then
        echo "\$ip"  # Si privée, on ne change rien
    else
        # Générer un identifiant unique basé sur l'IP pour obtenir une IP fictive cohérente
        # On utilise un simple hachage (somme des octets modulo 255) pour le dernier octet
        IFS='.' read -r -a octets <<< "\$ip"
        hash=\$(( (\${octets[0]} + \${octets[1]} + \${octets[2]} + \${octets[3]}) % 255 ))
        if [ \$hash -eq 0 ]; then
            hash=1  # Éviter 203.0.113.0
        fi
        echo "203.0.113.\$hash"
    fi
}

# Trouver le dernier numéro de fichier existant
if ls "\${BASE_OUTPUT_FILE}"_*"\${EXTENSION}" >/dev/null 2>&1; then
    COUNTER=\$(ls "\${BASE_OUTPUT_FILE}"_*"\${EXTENSION}" | grep -o '[0-9]\+' | sort -n | tail -1)
    COUNTER=\$((COUNTER + 1))
else
    COUNTER=1
fi

echo "Démarrage de la capture NAT à partir du fichier numéro \$COUNTER" >&2

while true; do
    OUTPUT_FILE="\${BASE_OUTPUT_FILE}_\${COUNTER}\${EXTENSION}"
    TIMESTAMP=\$(date "+%Y-%m-%d %H:%M:%S")
    CONNTRACK_OUTPUT=\$(timeout 5 conntrack -L --any-nat 2>/tmp/conntrack_err)
    CONNTRACK_STATUS=\$?
    IW_OUTPUT=\$(iw dev wlan0 station dump 2>/tmp/iw_err)
    IW_STATUS=\$?
    UDP_STATES=\$(cat "\$STATE_FILE" 2>/dev/null || echo '{}')

    {
        echo "\$TIMESTAMP"
        if [ \$IW_STATUS -eq 0 ]; then
            if [ -n "\$IW_OUTPUT" ]; then
                MAC_LIST=\$(echo "\$IW_OUTPUT" | awk '/^Station/ {print \$2}')
                if [ -n "\$MAC_LIST" ]; then
                    while IFS= read -r MAC || [ -n "\$MAC" ]; do
                        if [ -n "\$UDP_STATES" ] && [ "\$UDP_STATES" != "{}" ]; then
                            UDP_INFO=\$(echo "\$UDP_STATES" | jq -r --arg mac "\$MAC" '.[ \$mac] | if . then "State: \(.screen_state)" else "State: N/A" end')
                        else
                            UDP_INFO="State: N/A"
                        fi
                        echo "\$MAC  \$UDP_INFO"
                    done <<< "\$MAC_LIST"
                else
                    echo "Aucune adresse MAC trouvée dans la sortie d'iw"
                fi
            else
                echo "Aucune station connectée à wlan0"
            fi
        else
            echo "Erreur lors de l'exécution de 'iw dev wlan0 station dump' (code: \$IW_STATUS)"
        fi
        echo "----------------------------------------"
        if [ \$CONNTRACK_STATUS -eq 0 ]; then
            if [ -n "\$CONNTRACK_OUTPUT" ]; then
                # Traiter chaque ligne de CONNTRACK_OUTPUT pour anonymiser les IPs
                echo "\$CONNTRACK_OUTPUT" | while IFS= read -r line || [ -n "\$line" ]; do
                    # Ignorer les lignes vides
                    if [ -z "\$line" ]; then
                        continue
                    fi
                    # Recherche des IPs avec les motifs src= et dst=
                    src_ip=\$(echo "\$line" | grep -oP '(?<=src=)\d+\.\d+\.\d+\.\d+' | head -1)
                    dst_ip=\$(echo "\$line" | grep -oP '(?<=dst=)\d+\.\d+\.\d+\.\d+' | head -1)
                    src_ip2=\$(echo "\$line" | grep -oP '(?<=src=)\d+\.\d+\.\d+\.\d+' | tail -1)
                    dst_ip2=\$(echo "\$line" | grep -oP '(?<=dst=)\d+\.\d+\.\d+\.\d+' | tail -1)

                    # Anonymisation des IPs si elles sont publiques
                    anon_src_ip=\$(anonymize_ip "\$src_ip")
                    anon_dst_ip=\$(anonymize_ip "\$dst_ip")
                    anon_src_ip2=\$(anonymize_ip "\$src_ip2")
                    anon_dst_ip2=\$(anonymize_ip "\$dst_ip2")

                    # Remplacement des IPs dans la ligne
                    result="\$line"
                    if [ -n "\$src_ip" ]; then
                        result=\$(echo "\$result" | sed "s/src=\$src_ip/src=\$anon_src_ip/")
                    fi
                    if [ -n "\$dst_ip" ]; then
                        result=\$(echo "\$result" | sed "s/dst=\$dst_ip/dst=\$anon_dst_ip/")
                    fi
                    if [ -n "\$src_ip2" ] && [ "\$src_ip" != "\$src_ip2" ]; then
                        result=\$(echo "\$result" | sed "s/src=\$src_ip2/src=\$anon_src_ip2/")
                    fi
                    if [ -n "\$dst_ip2" ] && [ "\$dst_ip" != "\$dst_ip2" ]; then
                        result=\$(echo "\$result" | sed "s/dst=\$dst_ip2/dst=\$anon_dst_ip2/")
                    fi
                    echo "\$result"
                done
            else
                echo "Aucune connexion NAT détectée"
            fi
        else
            echo "Erreur lors de l'exécution de 'conntrack -L --any-nat' (code: \$CONNTRACK_STATUS)"
            cat /tmp/conntrack_err
        fi
        echo
    } > "\$OUTPUT_FILE"

    echo "Données enregistrées dans \$OUTPUT_FILE à \$TIMESTAMP" >&2
    rm -f /tmp/conntrack_err /tmp/iw_err
    ((COUNTER++))
    sleep "\$INTERVAL"
done
EOF

sudo chmod +x "$NAT_CAPTURE_SCRIPT"

# Service pour capture.sh
sudo bash -c "cat > /etc/systemd/system/nat-capture.service" <<EOF
[Unit]
Description=NAT Capture Service
After=network.target udp-server.service
[Service]
ExecStart=$NAT_CAPTURE_SCRIPT
WorkingDirectory=$CURRENT_DIR
Restart=always
StandardOutput=journal
StandardError=journal
[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable nat-capture.service
sudo systemctl start nat-capture.service

# Script de monitoring
MONITOR_SCRIPT="${CURRENT_DIR}/monitor.sh"
sudo bash -c "cat > $MONITOR_SCRIPT" <<EOF
#!/bin/bash
sleep 610

if [ "\$EUID" -ne 0 ]; then
    echo "Erreur : Exécuter avec sudo."
    exit 1
fi

WLAN_IFACE="wlan0"
ETH_IFACE="eth0"
NAT_CAPTURE_SCRIPT="$NAT_CAPTURE_SCRIPT"
UDP_SERVER_SCRIPT="$UDP_SERVER_SCRIPT"
NAT_LOG_DIR="$NAT_LOG_DIR"
CONFAP_SCRIPT="$CURRENT_DIR/confap.sh"

while true; do
    echo "Vérification en cours..."

    run_confap() {
        if [ -f "\$CONFAP_SCRIPT" ] && [ -x "\$CONFAP_SCRIPT" ]; then
            echo "Exécution de \$CONFAP_SCRIPT pour corriger le problème..."
            "\$CONFAP_SCRIPT"
        else
            echo "Erreur : \$CONFAP_SCRIPT introuvable ou non exécutable."
        fi
    }

    for service in hostapd dnsmasq nf_conntrack_acct udp-server nat-capture; do
        if ! systemctl is-active "\$service" >/dev/null 2>&1; then
            echo "Problème : \$service n'est pas actif."
            run_confap
            break
        fi
    done

    if ! ip addr show "\$WLAN_IFACE" | grep -q "10.20.10.1"; then
        echo "Problème : \$WLAN_IFACE n'a pas l'IP correcte."
        run_confap
    fi

    if ! iptables -t nat -C POSTROUTING -o "\$ETH_IFACE" -j MASQUERADE 2>/dev/null; then
        echo "Problème : Règle NAT absente."
        run_confap
    fi

    if ! sysctl net.ipv4.ip_forward | grep -q "1"; then
        echo "Problème : IP forwarding désactivé."
        run_confap
    fi

    if ! ping -I "\$ETH_IFACE" -c 4 8.8.8.8 >/dev/null 2>&1; then
        echo "Problème : Pas de connectivité Internet via \$ETH_IFACE."
        run_confap
    fi

    if [ ! -f "\$NAT_CAPTURE_SCRIPT" ] || [ ! -x "\$NAT_CAPTURE_SCRIPT" ] || ! systemctl is-active nat-capture >/dev/null; then
        echo "Problème : \$NAT_CAPTURE_SCRIPT ne fonctionne pas correctement."
        run_confap
    fi

    echo "Prochaine vérification dans 300 secondes..."
    sleep 300
done
EOF

sudo chmod +x "$MONITOR_SCRIPT"

# Service pour monitor.sh
sudo bash -c "cat > /etc/systemd/system/monitor.service" <<EOF
[Unit]
Description=Hotspot Monitoring Service
After=network.target nat-capture.service udp-server.service
[Service]
ExecStart=$MONITOR_SCRIPT
WorkingDirectory=$CURRENT_DIR
Restart=always
StandardOutput=journal
StandardError=journal
[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable monitor.service
sudo systemctl start monitor.service

echo "Hotspot configuration completed!"
echo "The SSID 'ecobox' will be available in about 1 minute."
echo "NAT capture script installed at $NAT_CAPTURE_SCRIPT and running as a systemd service."
echo "NAT logs will be stored in $NAT_LOG_DIR"
echo "Monitoring script installed at $MONITOR_SCRIPT and running as a systemd service."
echo "UDP server script installed at $UDP_SERVER_SCRIPT and running as a systemd service."


