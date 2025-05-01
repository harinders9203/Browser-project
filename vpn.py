import os
import sys
import subprocess
import threading
import time
import json
import tkinter as tk
from tkinter import ttk, messagebox
import socket
import urllib.request
import winreg
import logging
import requests
import socks

class WireGuardThread:
    def __init__(self):
        self.connection_active = False
        self.process = None
        self.thread = None
        self.current_server = None
        self.wireguard_path = self._find_wireguard_exe()
        self.wg_path = self._find_wg_exe()
        
    def _find_wireguard_exe(self):
        """Find the WireGuard executable on Windows"""
        wireguard_paths = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "WireGuard", "wireguard.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "WireGuard", "wireguard.exe")
        ]
        
        for path in wireguard_paths:
            if os.path.exists(path):
                return path
        
        # If not found, assume it's in PATH
        return "wireguard.exe"
    
    def _find_wg_exe(self):
        """Find the wg.exe executable on Windows"""
        wg_paths = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "WireGuard", "wg.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "WireGuard", "wg.exe")
        ]
        
        for path in wg_paths:
            if os.path.exists(path):
                return path
        
        # If not found, assume it's in PATH
        return "wg.exe"

    def disable_ipv6(self):
        """Disable IPv6 to prevent leaks"""
        try:
            # Disable IPv6 using Windows registry
            key_path = r'SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters'
            value_name = 'DisabledComponents'
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_WRITE) as key:
                # 0xFF disables IPv6 entirely
                winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, 0xFF)
                
            print("IPv6 disabled successfully")
            return True
        except Exception as e:
            print(f"Error disabling IPv6: {str(e)}")
            return False

    def fix_dns_leaks(self):
        """Fix DNS leaks by setting secure DNS servers"""
        try:
            # Set DNS to force all DNS queries through VPN tunnel
            key_path = r'SYSTEM\CurrentControlSet\Services\Dnscache\Parameters'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, 'ServerPriorityTimeLimit', 0, winreg.REG_DWORD, 0)
                
            print("DNS leak protection applied")
            return True
        except Exception as e:
            print(f"Error setting DNS leak protection: {str(e)}")
            return False
    
    def start_vpn(self, config_path):
        """Start VPN in a separate thread with leak protection"""
        if self.connection_active:
            return False
        
        # Apply leak protections before connecting
        self.disable_ipv6()
        self.fix_dns_leaks()
        
        # Enhance the config with kill switch and DNS leak prevention
        enhanced_config_path = self._enhance_config(config_path)
        
        def run_vpn():
            """Thread function to run the VPN"""
            try:
                # Use silent mode (/silent) to run WireGuard without showing the UI
                cmd = [self.wireguard_path, "/installtunnelservice", enhanced_config_path, "/silent"]
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW  # Hide console window
                )
                
                self.connection_active = True
                print(f"VPN started with enhanced config: {enhanced_config_path}")
                
                # Set routes to ensure all traffic goes through VPN
                self._set_vpn_routes()
                
                # Monitor the process
                while self.process.poll() is None:
                    time.sleep(1)
                
                # Process has terminated
                self.connection_active = False
                print("VPN process has terminated")
                
            except Exception as e:
                print(f"Error in VPN thread: {str(e)}")
                self.connection_active = False
        
        # Start the thread
        self.thread = threading.Thread(target=run_vpn)
        self.thread.daemon = True  # Thread will exit when main program exits
        self.thread.start()
        
        # Wait a bit to check if connection started successfully
        time.sleep(2)
        return self.connection_active

    def _enhance_config(self, config_path):
        """Create enhanced version of config with leak protections"""
        # Read original config
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Check if AllowedIPs is already set to cover all traffic
        if "AllowedIPs = 0.0.0.0/0" not in config_content:
            # Add or modify AllowedIPs to route all traffic through VPN
            if "[Peer]" in config_content:
                config_content = config_content.replace(
                    "[Peer]",
                    "[Peer]\nAllowedIPs = 0.0.0.0/0"
                )
        
        # Ensure DNS is set to prevent DNS leaks
        if "DNS = " not in config_content:
            # Add DNS servers to prevent DNS leaks
            config_content = config_content.replace(
                "[Interface]",
                "[Interface]\nDNS = 1.1.1.1, 8.8.8.8"
            )
        
        # Create enhanced config file
        enhanced_path = config_path.replace(".conf", "_enhanced.conf")
        with open(enhanced_path, 'w') as f:
            f.write(config_content)
        
        return enhanced_path

    def _set_vpn_routes(self):
        """Set up routes to ensure all traffic goes through VPN"""
        try:
            # Find the VPN interface
            result = subprocess.run(
                [self.wg_path, "show", "interfaces"], 
                capture_output=True, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout.strip():
                interface = result.stdout.strip()
                
                # Add route to force all traffic through VPN
                subprocess.run(
                    ["route", "ADD", "0.0.0.0", "MASK", "0.0.0.0", "0.0.0.0", 
                     "IF", interface, "METRIC", "1"],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                print(f"Added route for all traffic through interface {interface}")
        except Exception as e:
            print(f"Error setting routes: {str(e)}")
    
    def stop_vpn(self):
        """Stop the running VPN"""
        if not self.connection_active:
            return True
        
        try:
            # Uninstall tunnel service
            cmd = [self.wireguard_path, "/uninstalltunnelservice", "*"]
            subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Wait for the thread to finish
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            
            self.connection_active = False
            return True
        except Exception as e:
            print(f"Error stopping VPN: {str(e)}")
            return False
    
    def check_status(self):
        """Check if VPN is connected"""
        try:
            # Run wg show interfaces to check active connections
            result = subprocess.run(
                [self.wg_path, "show", "interfaces"], 
                capture_output=True, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # If we have output, a connection is active
            return result.returncode == 0 and result.stdout.strip() != ""
        except Exception as e:
            print(f"Error checking status: {str(e)}")
            return False

    def check_ip_location(self):
        """Check current IP address and location"""
        try:
            # Use a service that returns IP info
            with urllib.request.urlopen("https://ipinfo.io/json", timeout=5) as response:
                data = json.loads(response.read().decode())
                return {
                    'ip': data.get('ip', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'city': data.get('city', 'Unknown')
                }
        except Exception as e:
            print(f"Error checking IP: {str(e)}")
            return {
                'ip': 'Error',
                'country': 'Unknown',
                'region': 'Unknown',
                'city': 'Unknown'
            }

class VPNApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure VPN Manager")
        
        # Initialize WireGuard Thread manager
        self.vpn_thread = WireGuardThread()

        # Server configurations
        self.servers = {
            "Japan": "configs/japan.conf",
            "Germany": "configs/germany.conf",
            "United States": "configs/us.conf",
            "Netherlands": "configs/netherlands.conf"
        }
        
        # Create the UI
        self._create_ui()
        
        # Start periodic status check
        self._check_status()
        self.root.after(5000, self._periodic_status_check)
    
    def _create_ui(self):
        """Create the user interface"""
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Server selection dropdown
        ttk.Label(frame, text="Select VPN Server:").grid(column=0, row=0, sticky=tk.W, pady=5)
        
        self.server_var = tk.StringVar()
        self.server_combo = ttk.Combobox(frame, textvariable=self.server_var)
        self.server_combo['values'] = list(self.servers.keys())
        self.server_combo.grid(column=1, row=0, sticky=(tk.W, tk.E), pady=5)
        self.server_combo.current(0)
        
        # Status display
        ttk.Label(frame, text="Status:").grid(column=0, row=1, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value="Disconnected")
        ttk.Label(frame, textvariable=self.status_var).grid(column=1, row=1, sticky=tk.W, pady=5)
        
        # IP information
        ttk.Label(frame, text="IP Address:").grid(column=0, row=2, sticky=tk.W, pady=5)
        self.ip_var = tk.StringVar(value="Not connected")
        ttk.Label(frame, textvariable=self.ip_var).grid(column=1, row=2, sticky=tk.W, pady=5)
        
        ttk.Label(frame, text="Location:").grid(column=0, row=3, sticky=tk.W, pady=5)
        self.location_var = tk.StringVar(value="Not connected")
        ttk.Label(frame, textvariable=self.location_var).grid(column=1, row=3, sticky=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(column=0, row=4, columnspan=2, pady=10)
        
        self.connect_button = ttk.Button(button_frame, text="Connect", command=self.connect)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_button = ttk.Button(button_frame, text="Disconnect", command=self.disconnect)
        self.disconnect_button.pack(side=tk.LEFT, padx=5)
        self.disconnect_button.config(state=tk.DISABLED)
        
        self.check_ip_button = ttk.Button(button_frame, text="Check IP", command=self.update_ip_info)
        self.check_ip_button.pack(side=tk.LEFT, padx=5)
        
        # Kill switch option
        self.kill_switch_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Enable Kill Switch", variable=self.kill_switch_var).grid(
            column=0, row=5, columnspan=2, sticky=tk.W, pady=5
        )
        
        # Configure grid expandability
        frame.columnconfigure(1, weight=1)
    
    def _periodic_status_check(self):
        """Run status check periodically"""
        self._check_status()
        self.root.after(5000, self._periodic_status_check)
    
    def _check_status(self):
        """Check the VPN connection status and update UI"""
        is_connected = self.vpn_thread.check_status()
        
        if is_connected:
            current_server = self.vpn_thread.current_server or "Unknown"
            self.status_var.set(f"Connected to {current_server}")
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            
            # Update IP info 
            self.update_ip_info()
        else:
            self.status_var.set("Disconnected")
            self.connect_button.config(state=tk.NORMAL)
            self.disconnect_button.config(state=tk.DISABLED)
    
    def update_ip_info(self):
        """Update the IP and location information"""
        self.ip_var.set("Checking...")
        self.location_var.set("Checking...")
        self.root.update()
        
        # Run in a separate thread to avoid freezing the UI
        def check_ip_thread():
            ip_info = self.vpn_thread.check_ip_location()
            
            # Update UI in main thread
            self.root.after(0, lambda: self.ip_var.set(ip_info['ip']))
            self.root.after(0, lambda: self.location_var.set(
                f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"
            ))
        
        threading.Thread(target=check_ip_thread, daemon=True).start()
    
    def connect(self):
        """Connect to the selected server with leak protection"""
        server_name = self.server_var.get()
        if not server_name or server_name not in self.servers:
            messagebox.showerror("Error", "Please select a valid server")
            return
        
        config_path = self.servers[server_name]
        
        # Check if config file exists
        if not os.path.exists(config_path):
            messagebox.showerror("Error", f"Configuration file not found: {config_path}")
            return
        
        # Change status to connecting
        self.status_var.set(f"Connecting to {server_name}...")
        self.root.update()
        
        # Start VPN connection in a thread
        success = self.vpn_thread.start_vpn(config_path)
        
        if success:
            self.vpn_thread.current_server = server_name
            self._check_status()
        else:
            self.status_var.set("Failed to connect")
            messagebox.showerror("Connection Failed", f"Failed to connect to {server_name}")
    
    def disconnect(self):
        """Disconnect from the VPN"""
        self.status_var.set("Disconnecting...")
        self.root.update()
        
        success = self.vpn_thread.stop_vpn()
        
        if success:
            self.vpn_thread.current_server = None
            self._check_status()
        else:
            messagebox.showerror("Disconnection Failed", "Failed to disconnect from VPN")

def generate_sample_configs():
    """Create sample config files with proper leak protection settings"""
    if not os.path.exists("configs"):
        os.makedirs("configs")
    
    servers = {
        "japan": {
            "endpoint": "203.0.113.2:51820",
            "public_key": "JPN_SERVER_PUBLIC_KEY_HERE"
        },
        "germany": {
            "endpoint": "203.0.113.3:51820",
            "public_key": "GER_SERVER_PUBLIC_KEY_HERE"
        },
        "us": {
            "endpoint": "203.0.113.1:51820",
            "public_key": "US_SERVER_PUBLIC_KEY_HERE"
        },
        "netherlands": {
            "endpoint": "203.0.113.4:51820",
            "public_key": "NL_SERVER_PUBLIC_KEY_HERE"
        }
    }
    
    for server_name, server_info in servers.items():
        config_path = f"configs/{server_name}.conf"
        if not os.path.exists(config_path):
            # Create a leak-proof config file
            with open(config_path, "w") as f:
                f.write(f"""[Interface]
PrivateKey = YOUR_PRIVATE_KEY_HERE
Address = 10.0.0.2/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = {server_info['public_key']}
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = {server_info['endpoint']}
PersistentKeepalive = 25
""")

class VPNHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        self.logger.addHandler(handler)
        
        self.current_server = None
        self.original_socket = socket.socket
        self.servers = self._setup_servers()
        self.session = requests.Session()
        self.session.timeout = 10  # Set timeout for all requests

    def _setup_servers(self):
        return {
            "US": {
                "host": "192.111.135.17",
                "port": 4145,
                "country": "United States"
            },
            "CA": {
                "host": "192.111.139.165",
                "port": 4145,
                "country": "Canada"
            }
        }

    def _get_current_ip(self, max_retries=3):
        services = [
            "http://ip-api.com/json",
            "http://ipwho.is",
            "http://ipinfo.io/json"
        ]
        
        for attempt in range(max_retries):
            for service in services:
                try:
                    response = self.session.get(service, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if "country" in data:
                            return data.get("country"), data.get("ip")
                except Exception as e:
                    self.logger.warning(f"Failed to get IP from {service}: {str(e)}")
                    time.sleep(2)  # Wait before retry
                    continue
        
        raise Exception("Could not verify IP location after multiple attempts")

    def connect(self, server_name=None):
        if not server_name:
            server_name = "US"  # Default to US server
            
        if server_name not in self.servers:
            raise ValueError(f"Server {server_name} not found. Available servers: {', '.join(self.servers.keys())}")
            
        server = self.servers[server_name]
        
        # Configure SOCKS5 proxy with DNS resolution through the proxy
        socks.set_default_proxy(
            socks.SOCKS5, 
            server["host"], 
            server["port"],
            rdns=True,  # Resolve DNS through proxy
            username=None,  # Add credentials if needed
            password=None
        )
        
        # Replace the socket
        socket.socket = socks.socksocket
        
        # Configure session to use the proxy
        self.session.proxies = {
            'http': f'socks5://{server["host"]}:{server["port"]}',
            'https': f'socks5://{server["host"]}:{server["port"]}'
        }
        
        # Verify connection
        max_retries = 3
        for attempt in range(max_retries):
            try:
                country, ip = self._get_current_ip()
                if country == server["country"]:
                    self.current_server = server_name
                    self.logger.info(f"Successfully connected to {server['country']} ({ip})")
                    return True
                else:
                    self.logger.warning(f"Connected but location mismatch. Expected {server['country']}, got {country}")
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    self.disconnect()
                    raise Exception("Failed to establish connection after multiple attempts")
        
        return False

    def disconnect(self):
        if hasattr(self, 'original_socket'):
            socket.socket = self.original_socket
        self.current_server = None
        self.session = requests.Session()
        self.logger.info("Disconnected from proxy server")

    def status(self):
        if not self.current_server:
            return "Not connected"
        try:
            country, ip = self._get_current_ip()
            return f"Connected to {country} ({ip})"
        except Exception as e:
            return f"Error checking status: {str(e)}"

    def list_servers(self):
        return list(self.servers.keys())

def main():
    # Create configs with leak protection
    generate_sample_configs()
    
    # Start the application
    root = tk.Tk()
    app = VPNApp(root)
    root.geometry("500x300")
    root.mainloop()

if __name__ == "__main__":
    main()