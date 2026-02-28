from collections import defaultdict
import re
import os
import csv
from datetime import datetime

def parse_nat(line):
    pattern = r"""
        ^(?P<protocol>tcp|udp)\s+
        (?P<proto_num>\d+)\s+
        (?P<ttl>\d+)\s+
        (?P<state>[A-Z_]+)?\s*
        src=(?P<src_ip>\d+\.\d+\.\d+\.\d+)\s+
        dst=(?P<dst_ip>\d+\.\d+\.\d+\.\d+)\s+
        sport=(?P<sport>\d+)\s+
        dport=(?P<dport>\d+)\s+
        packets=(?P<packets1>\d+)\s+
        bytes=(?P<bytes1>\d+)\s+
        src=(?P<src_ip2>\d+\.\d+\.\d+\.\d+)\s+
        dst=(?P<dst_ip2>\d+\.\d+\.\d+\.\d+)\s+
        sport=(?P<sport2>\d+)\s+
        dport=(?P<dport2>\d+)\s+
        packets=(?P<packets2>\d+)\s+
        bytes=(?P<bytes2>\d+)\s+
        (?:\[?(?P<flags>[A-Z]+)\])?\s*
        mark=(?P<mark>\d+)\s+
        use=(?P<use>\d+)$
    """
    regex = re.compile(pattern, re.VERBOSE)
    match = regex.match(line.strip())
    return match.groupdict() if match else None

def average_packets(folder_path, interval):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    for filename in files:
        device_packets = defaultdict(int)
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            print(file)
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            has_data = False
            
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    has_data = True
                    if result['state'] == 'ESTABLISHED' or result['protocol'] == 'udp':
                        packets1 = int(result['packets1'])
                        packets2 = int(result['packets2'])
                        device_packets[result['src_ip']] += packets1 + packets2
            
            avg = 0
            if has_data:
                max_total_packets = max(device_packets.values(), default=0)
                avg = max_total_packets / interval
            results[filename] = avg
    return results

def average_packets_per_device(folder_path, interval):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    for filename in files:
        device_packets = defaultdict(int)
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            has_data = False
            
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    has_data = True
                    if result['state'] in ('ESTABLISHED', 'None') or result['protocol'] == 'udp':
                        packets1 = int(result['packets1'])
                        packets2 = int(result['packets2'])
                        device_packets[result['src_ip']] += packets1 + packets2
            
            avg = 0
            if has_data:
                max_total_packets = max(device_packets.values(), default=0)
                num_devices = len(device_packets)
                avg = (max_total_packets / interval) / num_devices if num_devices else 0
            results[filename] = avg
    return results

def average_connections(folder_path, interval):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    for filename in files:
        device_connections = defaultdict(int)
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            has_data = False
            
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    has_data = True
                    if result['state'] in ('ESTABLISHED', 'None') or result['protocol'] == 'udp':
                        device_connections[result['src_ip']] += 1
            
            avg = 0
            if has_data:
                max_connections = max(device_connections.values(), default=0)
                avg = max_connections / interval
            results[filename] = avg
    return results

def average_connections_per_device(folder_path, interval):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    for filename in files:
        device_connections = defaultdict(int)
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            has_data = False
            
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    has_data = True
                    if result['state'] in ('ESTABLISHED', 'None') or result['protocol'] == 'udp':
                        device_connections[result['src_ip']] += 1
            
            avg = 0
            if has_data:
                max_connections = max(device_connections.values(), default=0)
                avg = (max_connections / interval) / len(device_connections) if len(device_connections) else 0
            results[filename] = avg
    return results

def average_throughput_per_device(folder_path, interval):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    for filename in files:
        device_bytes = defaultdict(int)
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            has_data = False
            
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    has_data = True
                    if result['state'] == 'ESTABLISHED' or result['protocol'] == 'udp':
                        bytes1 = int(result['bytes1'])
                        bytes2 = int(result['bytes2'])
                        device_bytes[result['src_ip']] += bytes1 + bytes2
            
            throughput = 0
            if has_data:
                max_throughput = max(device_bytes.values(), default=0)
                throughput = (max_throughput / interval) / len(device_bytes) if len(device_bytes) else 0
            results[filename] = throughput
    return results

def max_throughput_per_device(folder_path, interval):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    for filename in files:
        device_bytes = defaultdict(int)
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            has_data = False
            
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    has_data = True
                    if result['state'] == 'ESTABLISHED' or result['protocol'] == 'udp':
                        bytes1 = int(result['bytes1'])
                        bytes2 = int(result['bytes2'])
                        device_bytes[result['src_ip']] += bytes1 + bytes2
            
            throughput = 0
            if has_data:
                max_throughput = max(device_bytes.values(), default=0)
                throughput = max_throughput / interval
            results[filename] = throughput
    return results

def count_connected_devices_actif(folder_path):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    for filename in files:
        devices = set()
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            has_data = False
            
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    has_data = True
                    devices.add(result['src_ip'])
            
            num_devices = len(devices) if has_data else 0
            results[filename] = num_devices
    return results

def count_connected_devices_by_mac(folder_path):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    for filename in files:
        mac_addresses = set()
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                line = line.strip()
                if line == "----------------------------------------":
                    break
                mac_match = re.match(r'^([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})\s+State:\s+\w+$', line)
                if mac_match:
                    mac_addresses.add(mac_match.group(1))
            
            num_devices = len(mac_addresses)
            results[filename] = num_devices
    return results

def average_packet_size(folder_path, interval):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    excluded_ports = {1, 2, 3, 4, 5}  # Ports à exclure pour UDP
    
    for filename in files:
        device_bytes = defaultdict(int)
        device_packets = defaultdict(int)
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            has_data = False
            
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    sport = int(result['sport'])
                    dport = int(result['dport'])
                    # Exclure les ports uniquement pour UDP
                    if (result['protocol'] == 'tcp' and result['state'] == 'ESTABLISHED') or \
                       (result['protocol'] == 'udp' and sport not in excluded_ports and dport not in excluded_ports):
                        has_data = True
                        bytes1 = int(result['bytes1'])
                        bytes2 = int(result['bytes2'])
                        packets1 = int(result['packets1'])
                        packets2 = int(result['packets2'])
                        src_ip = result['src_ip']
                        device_bytes[src_ip] += bytes1 + bytes2
                        device_packets[src_ip] += packets1 + packets2
            
            avg_size = 0
            if has_data:
                max_packets = max(device_packets.values(), default=0)
                max_bytes = max(device_bytes.values(), default=0)
                avg_size = (max_bytes / max_packets if max_packets else 0) / interval
            results[filename] = avg_size
    return results

def count_active_connections(folder_path):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    excluded_ports = {1, 2, 3, 4, 5}  # Ports à exclure pour UDP
    
    for filename in files:
        active_connections = set()
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            has_data = False
            
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    sport = int(result['sport'])
                    dport = int(result['dport'])
                    # Exclure les ports uniquement pour UDP
                    if (result['protocol'] == 'tcp' and result['state'] == 'ESTABLISHED') or \
                       (result['protocol'] == 'udp' and sport not in excluded_ports and dport not in excluded_ports):
                        has_data = True
                        src_ip = result['src_ip']
                        sport = result['sport']
                        dport = result['dport']
                        active_connections.add((src_ip, sport, dport))
            
            num_active = len(active_connections) if has_data else 0
            results[filename] = num_active
    return results

def calculate_connection_ratios(folder_path):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    for filename in files:
        timewait_count = 0
        established_count = 0
        udp_count = 0
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            has_data = False
            
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    has_data = True
                    protocol = result['protocol']
                    state = result.get('state', None)
                    if protocol == 'tcp':
                        if state == 'TIME_WAIT':
                            timewait_count += 1
                        elif state == 'ESTABLISHED':
                            established_count += 1
                    elif protocol == 'udp':
                        udp_count += 1
            
            ratio = 0
            if has_data:
                ratio = timewait_count / (established_count + udp_count) if (established_count + udp_count) > 0 else 0
            results[filename] = ratio
    return results

def categorize_nat_files_by_time_block(folder_path):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    for filename in files:
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r') as f:
            timestamp = f.readline().strip()
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            block = (dt.hour // 2) + 1
            results[filename] = block
    return results

def analyze_new_connections_max_per_device(folder_path, start_file_number=5):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    files = [f for f in files if extract_number_from_filename(f) >= start_file_number]
    
    previous_connections = set()
    
    for i, filename in enumerate(files):
        tcp_connections = defaultdict(int)
        udp_connections = defaultdict(int)
        file_path = os.path.join(folder_path, filename)
        
        current_connections = set()
        has_data = False
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    has_data = True
                    protocol = result['protocol']
                    state = result.get('state', None)
                    src_ip = result['src_ip']
                    dst_ip = result['dst_ip']
                    sport = result['sport']
                    dport = result['dport']
                    conn_tuple = (src_ip, dst_ip, sport, dport)
                    current_connections.add(conn_tuple)
                    is_new = conn_tuple not in previous_connections or i == 0
                    if protocol == 'tcp' and state == 'ESTABLISHED' and is_new:
                        tcp_connections[src_ip] += 1
                    elif protocol == 'udp' and is_new:
                        udp_connections[src_ip] += 1
            
            max_tcp = max(tcp_connections.values(), default=0) if has_data else 0
            max_udp = max(udp_connections.values(), default=0) if has_data else 0
            results[filename] = {"max_tcp": max_tcp, "max_udp": max_udp}
            previous_connections = current_connections
    return results

def time_since_last_new_connection(folder_path, interval, display_start_file_number=5):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    last_new_connection_time_tcp = defaultdict(lambda: None)
    last_new_connection_time_udp = defaultdict(lambda: None)
    previous_connections_tcp = defaultdict(set)
    previous_connections_udp = defaultdict(set)
    
    for i, filename in enumerate(files):
        current_file_number = extract_number_from_filename(filename)
        file_path = os.path.join(folder_path, filename)
        
        current_connections_tcp = defaultdict(set)
        current_connections_udp = defaultdict(set)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            has_data = False
            
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    has_data = True
                    protocol = result['protocol']
                    state = result.get('state', None)
                    src_ip = result['src_ip']
                    dst_ip = result['dst_ip']
                    sport = result['sport']
                    dport = result['dport']
                    conn_tuple = (dst_ip, sport, dport)
                    if protocol == 'tcp' and state == 'ESTABLISHED':
                        current_connections_tcp[src_ip].add(conn_tuple)
                    elif protocol == 'udp':
                        current_connections_udp[src_ip].add(conn_tuple)
        
        if current_file_number >= display_start_file_number and has_data:
            all_devices = set(current_connections_tcp.keys()) | set(current_connections_udp.keys())
            tcp_duration = 0
            udp_duration = 0
            if all_devices:
                device_durations = {}
                for device_ip in all_devices:
                    new_tcp_conns = current_connections_tcp[device_ip] - previous_connections_tcp[device_ip]
                    if new_tcp_conns or last_new_connection_time_tcp[device_ip] is None:
                        last_new_connection_time_tcp[device_ip] = current_file_number
                    
                    last_tcp_file = last_new_connection_time_tcp[device_ip]
                    tcp_dur = 0 if last_tcp_file is None else (current_file_number - last_tcp_file) * interval / 2
                    
                    new_udp_conns = current_connections_udp[device_ip] - previous_connections_udp[device_ip]
                    if new_udp_conns or last_new_connection_time_udp[device_ip] is None:
                        last_new_connection_time_udp[device_ip] = current_file_number
                    
                    last_udp_file = last_new_connection_time_udp[device_ip]
                    udp_dur = 0 if last_udp_file is None else (current_file_number - last_udp_file) * interval / 2
                    
                    device_durations[device_ip] = (tcp_dur, udp_dur)
                
                min_tcp = min(d[0] for d in device_durations.values()) if device_durations else 0
                min_udp = min(d[1] for d in device_durations.values()) if device_durations else 0
                tcp_duration = min_tcp
                udp_duration = min_udp
            results[filename] = {"tcp_duration": tcp_duration, "udp_duration": udp_duration}
        previous_connections_tcp = current_connections_tcp
        previous_connections_udp = current_connections_udp
    return results

def average_session_duration(folder_path, interval, display_start_file_number=5):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    connection_history_tcp = defaultdict(dict)
    connection_history_udp = defaultdict(dict)
    
    for filename in files:
        file_number = extract_number_from_filename(filename)
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            print(file)
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    protocol = result['protocol']
                    state = result.get('state', None)
                    src_ip = result['src_ip']
                    dst_ip = result['dst_ip']
                    sport = result['sport']
                    dport = result['dport']
                    conn_tuple = (dst_ip, sport, dport)
                    if protocol == 'tcp' and state == 'ESTABLISHED':
                        if file_number not in connection_history_tcp[src_ip]:
                            connection_history_tcp[src_ip][file_number] = set()
                        connection_history_tcp[src_ip][file_number].add(conn_tuple)
                    elif protocol == 'udp':
                        if file_number not in connection_history_udp[src_ip]:
                            connection_history_udp[src_ip][file_number] = set()
                        connection_history_udp[src_ip][file_number].add(conn_tuple)
    
    for i, filename in enumerate(files[:-1]):
        current_file_number = extract_number_from_filename(filename)
        previous_file_number = extract_number_from_filename(files[i - 1]) if i > 0 else None
        print(filename)
        if current_file_number < display_start_file_number:
            continue
        
        all_devices = set(connection_history_tcp.keys()) | set(connection_history_udp.keys())
        tcp_duration = 0
        udp_duration = 0
        
        if all_devices and previous_file_number is not None:
            total_tcp_duration_finished = 0
            total_tcp_finished = 0
            total_udp_duration_finished = 0
            total_udp_finished = 0
            total_tcp_duration_active = 0
            total_tcp_active = 0
            total_udp_duration_active = 0
            total_udp_active = 0
            
            for device_ip in all_devices:
                current_tcp = connection_history_tcp[device_ip].get(current_file_number, set())
                current_udp = connection_history_udp[device_ip].get(current_file_number, set())
                previous_tcp = connection_history_tcp[device_ip].get(previous_file_number, set())
                previous_udp = connection_history_udp[device_ip].get(previous_file_number, set())
                
                finished_tcp = previous_tcp - current_tcp
                finished_udp = previous_udp - current_udp
                
                if finished_tcp:
                    for conn in finished_tcp:
                        for file_num in sorted(connection_history_tcp[device_ip].keys()):
                            if conn in connection_history_tcp[device_ip][file_num]:
                                total_tcp_duration_finished += (previous_file_number - file_num + 1) * interval
                                total_tcp_finished += 1
                                break
                
                if finished_udp:
                    for conn in finished_udp:
                        for file_num in sorted(connection_history_udp[device_ip].keys()):
                            if conn in connection_history_udp[device_ip][file_num]:
                                total_udp_duration_finished += (previous_file_number - file_num + 1) * interval
                                total_udp_finished += 1
                                break
                
                if current_tcp:
                    for conn in current_tcp:
                        for file_num in sorted(connection_history_tcp[device_ip].keys()):
                            if conn in connection_history_tcp[device_ip][file_num]:
                                total_tcp_duration_active += (current_file_number - file_num + 1) * interval
                                total_tcp_active += 1
                                break
                
                if current_udp:
                    for conn in current_udp:
                        for file_num in sorted(connection_history_udp[device_ip].keys()):
                            if conn in connection_history_udp[device_ip][file_num]:
                                total_udp_duration_active += (current_file_number - file_num + 1) * interval
                                total_udp_active += 1
                                break
            
            if total_tcp_finished > 0:
                tcp_duration = (total_tcp_duration_finished / total_tcp_finished) / 2
            elif total_tcp_active > 0:
                tcp_duration = total_tcp_duration_active / total_tcp_active
            
            if total_udp_finished > 0:
                udp_duration = (total_udp_duration_finished / total_udp_finished) / 2
            elif total_udp_active > 0:
                udp_duration = total_udp_duration_active / total_udp_active
        
        results[filename] = {"tcp_duration": tcp_duration, "udp_duration": udp_duration}
    return results

def time_since_last_packet(folder_path, interval, display_start_file_number=5):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    excluded_ports = {1, 2, 3, 4, 5}  # Ports à exclure pour UDP
    
    connection_history = defaultdict(dict)
    
    for filename in files:
        file_number = extract_number_from_filename(filename)
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r') as file:
            next(file)
            for line in file:
                if line.strip() == "----------------------------------------":
                    break
            for line in file:
                if line.strip() == "Aucune connexion NAT détectée":
                    break
                result = parse_nat(line)
                if result:
                    protocol = result['protocol']
                    state = result.get('state', None)
                    src_ip = result['src_ip']
                    dst_ip = result['dst_ip']
                    sport = int(result['sport'])
                    dport = int(result['dport'])
                    packets1 = result['packets1']
                    packets2 = result['packets2']
                    conn_tuple = (dst_ip, sport, dport, packets1, packets2)
                    # Exclure les ports uniquement pour UDP
                    if (protocol == 'tcp' and state == 'ESTABLISHED') or \
                       (protocol == 'udp' and sport not in excluded_ports and dport not in excluded_ports):
                        if file_number not in connection_history[src_ip]:
                            connection_history[src_ip][file_number] = set()
                        connection_history[src_ip][file_number].add(conn_tuple)
    
    for i, filename in enumerate(files):
        current_file_number = extract_number_from_filename(filename)
        if current_file_number < display_start_file_number:
            continue
        
        all_devices = set(connection_history.keys())
        elapsed_time = 0
        
        if all_devices:
            current_connections = set()
            for device_ip in all_devices:
                current_connections |= connection_history[device_ip].get(current_file_number, set())
            
            if not current_connections:
                last_activity_file = None
                for j in range(i - 1, -1, -1):
                    previous_file_number = extract_number_from_filename(files[j])
                    previous_connections = set()
                    for device_ip in all_devices:
                        previous_connections |= connection_history[device_ip].get(previous_file_number, set())
                    if previous_connections:
                        last_activity_file = previous_file_number
                        break
                if last_activity_file is not None:
                    file_gap = current_file_number - last_activity_file
                    elapsed_time = (file_gap * interval) / 2
            else:
                last_activity_file = None
                if i > 0:
                    previous_file_number = extract_number_from_filename(files[i - 1])
                    previous_connections = set()
                    for device_ip in all_devices:
                        previous_connections |= connection_history[device_ip].get(previous_file_number, set())
                    
                    if current_connections != previous_connections:
                        last_activity_file = previous_file_number
                    else:
                        for j in range(i - 2, -1, -1):
                            prev_file_number = extract_number_from_filename(files[j])
                            prev_connections = set()
                            for device_ip in all_devices:
                                prev_connections |= connection_history[device_ip].get(prev_file_number, set())
                            if prev_connections and current_connections != prev_connections:
                                last_activity_file = prev_file_number
                                break
                
                if last_activity_file is None:
                    last_activity_file = current_file_number
                
                file_gap = current_file_number - last_activity_file
                elapsed_time = (file_gap * interval) / 2
        
        results[filename] = elapsed_time
    return results

def device_screen_state(folder_path):
    results = {}
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    def extract_number_from_filename(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1
    
    files.sort(key=extract_number_from_filename)
    
    for filename in files:
        file_path = os.path.join(folder_path, filename)
        has_on_or_na = False
        has_locked_with_traffic = False
        no_devices = False
        
        with open(file_path, 'r') as file:
            next(file)  # Ignorer le timestamp
            # Vérifier les états avant le séparateur
            for line in file:
                line = line.strip()
                if line == "----------------------------------------":
                    break
                if "State: On" in line or "State: N/A" in line:
                    has_on_or_na = True
                    break
                if "State: Locked" in line:
                    has_locked_with_traffic = True
                    # On continue pour vérifier le trafic plus tard
                    pass
                if line == "Aucune station connectée à wlan0":
                    no_devices = True
                    break
        
        # Déterminer la valeur à retourner
        if has_on_or_na:
            results[filename] = 1  # "ON" ou "N/A" donne 1
        elif no_devices:
            results[filename] = 0  # "Aucune station connectée à wlan0" donne 0
        else:
            results[filename] = 0
    
    return results

def generate_dataset(folder_path, interval=30, start_file_number=5):
    # Exécuter toutes les fonctions et collecter les résultats
    print("1:")
    avg_packets = average_packets(folder_path, interval)
    print("2:")
    avg_packets_per_dev = average_packets_per_device(folder_path, interval)
    print("3:")
    avg_connections = average_connections(folder_path, interval)
    print("4:")
    avg_conn_per_dev = average_connections_per_device(folder_path, interval)
    print("5:")
    avg_throughput = average_throughput_per_device(folder_path, interval)
    print("6:")
    max_throughput = max_throughput_per_device(folder_path, interval)
    print("7:")
    devices_actif = count_connected_devices_actif(folder_path)
    print("8:")
    devices_by_mac = count_connected_devices_by_mac(folder_path)
    print("9:")
    avg_packet_size_res = average_packet_size(folder_path, interval)
    print("10:")
    active_connections = count_active_connections(folder_path)
    print("11:")
    conn_ratios = calculate_connection_ratios(folder_path)
    print("12:")
    time_blocks = categorize_nat_files_by_time_block(folder_path)
    print("13:")
    new_connections = analyze_new_connections_max_per_device(folder_path, start_file_number)
    print("14:")
    time_since_conn = time_since_last_new_connection(folder_path, interval, start_file_number)
    print("15:")
    session_duration = average_session_duration(folder_path, interval, start_file_number)
    print("16:")
    time_since_packet = time_since_last_packet(folder_path, interval, start_file_number)
    print("17:")
    device_state = device_screen_state(folder_path)

    # Liste complète des fichiers
    files = sorted([f for f in os.listdir(folder_path) if f.endswith(".txt")], key=lambda x: int(re.search(r'(\d+)', x).group(1)) if re.search(r'(\d+)', x) else -1)
    
    # Headers du CSV sans "Filename" et "Timestamp"
    headers = [
        "Time Block", "Average Packets", "Average Packets per Device",
        "Average Connections", "Average Connections per Device", "Average Throughput per Device",
        "Max Throughput per Device", "Active Devices (IP)", "Connected Devices (MAC)",
        "Average Packet Size", "Active Connections", "Ratio TIME_WAIT/ESTABLISHED",
        "Max TCP Connections", "Max UDP Connections", "Time Since Last TCP Connection",
        "Time Since Last UDP Connection", "Average TCP Session Duration",
        "Average UDP Session Duration", "Time Since Last Packet", "Device Screen State"
    ]
    
    # Construire le dataset sans "Filename" et "Timestamp"
    dataset = []
    for filename in files:
        row = {
            "Time Block": time_blocks.get(filename, "N/A"),
            "Average Packets": avg_packets.get(filename, 0),
            "Average Packets per Device": avg_packets_per_dev.get(filename, 0),
            "Average Connections": avg_connections.get(filename, 0),
            "Average Connections per Device": avg_conn_per_dev.get(filename, 0),
            "Average Throughput per Device": avg_throughput.get(filename, 0),
            "Max Throughput per Device": max_throughput.get(filename, 0),
            "Active Devices (IP)": devices_actif.get(filename, 0),
            "Connected Devices (MAC)": devices_by_mac.get(filename, 0),
            "Average Packet Size": avg_packet_size_res.get(filename, 0),
            "Active Connections": active_connections.get(filename, 0),
            "Ratio TIME_WAIT/ESTABLISHED": conn_ratios.get(filename, 0),
            "Max TCP Connections": new_connections.get(filename, {"max_tcp": 0})["max_tcp"],
            "Max UDP Connections": new_connections.get(filename, {"max_udp": 0})["max_udp"],
            "Time Since Last TCP Connection": time_since_conn.get(filename, {"tcp_duration": 0})["tcp_duration"],
            "Time Since Last UDP Connection": time_since_conn.get(filename, {"udp_duration": 0})["udp_duration"],
            "Average TCP Session Duration": session_duration.get(filename, {"tcp_duration": 0})["tcp_duration"],
            "Average UDP Session Duration": session_duration.get(filename, {"udp_duration": 0})["udp_duration"],
            "Time Since Last Packet": time_since_packet.get(filename, 0),
            "Device Screen State": device_state.get(filename, 0)
        }
        print(row)
        dataset.append(row)
    
    # Écrire dans un fichier CSV
    with open("test4G.csv", 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(dataset)
    
    print("Dataset généré avec succès dans 'testnewmetric.csv'")

if __name__ == "__main__":
    interval = 30
    generate_dataset("test/avec4G", interval=30, start_file_number=5)




#27028

#20884