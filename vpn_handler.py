from PyQt5.QtCore import QObject, pyqtSignal
import subprocess
import sys
import os
import json
import time
import requests
import socket
import threading
import tempfile
import platform

class VPNHandler(QObject):
    status_changed = pyqtSignal(bool, str)  # Emits (is_connected, message)
    
    def __init__(self):
        super().__init__()
        self.config_dir = "./vpn_config"
        self.config_file = os.path.join(self.config_dir, "vpn_settings.json")
        self.is_connected = False
        self.current_server = None
        self.vpn_process = None
        self.load_config()
        self.openvpn_path = self._find_openvpn()
        
    def _find_openvpn(self):
        """Find OpenVPN executable path based on the operating system."""
        system = platform.system().lower()
        if system == 'windows':
            paths = [
                r"C:\Program Files\OpenVPN\bin\openvpn.exe",
                r"C:\Program Files (x86)\OpenVPN\bin\openvpn.exe"
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
        elif system == 'linux':
            return "/usr/sbin/openvpn"
        elif system == 'darwin':  # macOS
            return "/usr/local/sbin/openvpn"
        return None

    def load_config(self):
        """Load VPN configuration from file."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.servers = config.get('servers', self.get_default_servers())
            else:
                self.servers = self.get_default_servers()
                self.save_config()
        except Exception as e:
            print(f"Error loading VPN config: {e}")
            self.servers = self.get_default_servers()

    def save_config(self):
        """Save VPN configuration to file."""
        try:
            config = {
                'servers': self.servers
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving VPN config: {e}")

    def get_default_servers(self):
        """Return a list of default free VPN servers."""
        return [
            {
                'name': 'VPNGate Japan',
                'config_url': 'https://www.vpngate.net/common/openvpn_download.aspx?sid=5076014&host=public-vpn-40.opengw.net&port=443&hid=12199527',
                'country': 'Japan'
            },
            {
                'name': 'VPNGate US',
                'config_url': 'https://www.vpngate.net/common/openvpn_download.aspx?sid=5076016&host=public-vpn-172.opengw.net&port=443&hid=12199529',
                'country': 'United States'
            }
        ]

    def _download_config(self, server):
        """Download OpenVPN configuration file for the selected server."""
        try:
            response = requests.get(server['config_url'], timeout=10)
            if response.status_code == 200:
                config_path = os.path.join(self.config_dir, f"{server['name'].lower().replace(' ', '_')}.ovpn")
                with open(config_path, 'wb') as f:
                    f.write(response.content)
                return config_path
        except Exception as e:
            print(f"Error downloading config: {e}")
        return None

    def get_current_ip(self):
        """Get current public IP address."""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except:
            return "Unknown"

    def connect(self, server_index=0):
        """Connect to VPN server."""
        if self.is_connected:
            self.status_changed.emit(True, "Already connected to VPN")
            return

        if not self.openvpn_path:
            self.status_changed.emit(False, "OpenVPN not found. Please install OpenVPN first.")
            return

        try:
            server = self.servers[server_index]
            self.current_server = server
            
            # Get original IP
            original_ip = self.get_current_ip()
            self.status_changed.emit(False, f"Current IP: {original_ip}")
            
            # Download config if needed
            config_path = os.path.join(self.config_dir, f"{server['name'].lower().replace(' ', '_')}.ovpn")
            if not os.path.exists(config_path):
                self.status_changed.emit(False, "Downloading VPN configuration...")
                config_path = self._download_config(server)
                if not config_path:
                    raise Exception("Failed to download VPN configuration")

            # Start OpenVPN process
            self.status_changed.emit(False, "Connecting to VPN...")
            startupinfo = None
            if platform.system().lower() == 'windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.vpn_process = subprocess.Popen(
                [self.openvpn_path, '--config', config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo
            )

            # Wait for connection
            time.sleep(5)  # Give OpenVPN some time to connect
            
            # Verify IP change
            new_ip = self.get_current_ip()
            if new_ip == original_ip:
                raise Exception("IP address did not change")
            
            self.is_connected = True
            self.status_changed.emit(True, f"Connected to {server['name']} (IP: {new_ip})")
            
        except Exception as e:
            if self.vpn_process:
                self.vpn_process.terminate()
                self.vpn_process = None
            self.is_connected = False
            self.status_changed.emit(False, f"Failed to connect: {str(e)}")

    def disconnect(self):
        """Disconnect from VPN."""
        if not self.is_connected:
            self.status_changed.emit(False, "Not connected to VPN")
            return

        try:
            if self.vpn_process:
                self.vpn_process.terminate()
                self.vpn_process = None
            
            time.sleep(2)  # Give time for the connection to close
            current_ip = self.get_current_ip()
            
            self.is_connected = False
            self.current_server = None
            self.status_changed.emit(False, f"Disconnected from VPN (IP: {current_ip})")
            
        except Exception as e:
            self.status_changed.emit(False, f"Error disconnecting: {str(e)}")

    def toggle_connection(self):
        """Toggle VPN connection on/off."""
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()

    def get_status(self):
        """Get current VPN status."""
        if self.is_connected and self.current_server:
            try:
                current_ip = self.get_current_ip()
                return True, f"Connected to {self.current_server['name']} (IP: {current_ip})"
            except:
                return True, f"Connected to {self.current_server['name']}"
        return False, "Not connected"

    def cleanup(self):
        """Clean up VPN connection on application exit."""
        if self.is_connected:
            self.disconnect() 