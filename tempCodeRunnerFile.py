import requests
import socks
import socket
import json
import os
import logging
import time
from typing import Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal
import urllib3
import ssl

class VPNHandler(QObject):
    status_changed = pyqtSignal(bool, str)  # Signal to emit status updates (is_connected, message)
    
    def __init__(self):
        super().__init__()
        self.config_dir = "./vpn_config"
        self.config_file = os.path.join(self.config_dir, "vpn_settings.json")
        self.is_connected = False
        self.current_server = None
        self.original_socket = None
        self.original_getaddrinfo = None
        self.session = None
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("VPNHandler")

    def _test_socks_connection(self, host, port, timeout=10):
        """Test if we can establish a connection to the SOCKS5 server"""
        try:
            # Create a test socket
            test_socket = socks.socksocket()
            test_socket.settimeout(timeout)
            test_socket.set_proxy(socks.SOCKS5, host, port)
            
            # Try to connect to a known working server (Cloudflare DNS)
            test_socket.connect(("1.1.1.1", 53))
            test_socket.close()
            return True
        except Exception as e:
            self.logger.error(f"SOCKS5 connection test failed: {str(e)}")
            return False

    def _create_session(self, proxy_host, proxy_port):
        session = requests.Session()
        
        # Configure SOCKS5 proxy for all protocols
        proxy_url = f'socks5h://{proxy_host}:{proxy_port}'
        session.proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # Force direct DNS resolution instead of using Google DNS
        session.trust_env = False
        
        # Add headers to prevent DNS leaks
        session.headers.update({
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        return session

    def _get_current_ip(self):
        """Get current IP information with multiple service verification"""
        if not self.session:
            if self.is_connected and self.current_server:
                self.session = self._create_session(self.current_server['host'], self.current_server['port'])
            else:
                self.session = requests.Session()

        # List of IP checking services in order of preference
        services = [
            ('https://api64.ipify.org?format=json', lambda r: (r['ip'], 'Unknown', 'Unknown')),
            ('https://api.myip.com', lambda r: (r['ip'], 'Unknown', r['country'])),
            ('https://ipapi.co/json/', lambda r: (r['ip'], r['city'], r['country_name'])),
            ('https://ipinfo.io/json', lambda r: (r['ip'], r.get('city', 'Unknown'), r.get('country', 'Unknown')))
        ]

        errors = []
        for url, parser in services:
            try:
                self.logger.info(f"Trying IP service: {url}")
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.logger.info(f"Successfully got IP info from {url}")
                    return parser(data)
            except Exception as e:
                error_msg = f"{url}: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                continue

        self.logger.error(f"All IP services failed: {'; '.join(errors)}")
        return None

    def get_default_servers(self) -> Dict[str, dict]:
        """Return a dictionary of default VPN servers."""
        return {
            "US Elite 1": {
                "host": "67.201.39.14",
                "port": 4145,
                "name": "US Elite 1",
                "country": "United States"
            },
            "US Elite 2": {
                "host": "199.102.104.70",
                "port": 4145,
                "name": "US Elite 2",
                "country": "United States"
            },
            "Singapore Elite": {
                "host": "8.215.15.163",
                "port": 4145,
                "name": "Singapore Elite",
                "country": "Singapore"
            }
        }

    def _setup_proxy(self, server):
        """Set up system-wide SOCKS5 proxy"""
        try:
            # Configure SOCKS5 proxy
            socks.set_default_proxy(
                proxy_type=socks.SOCKS5,
                addr=server['host'],
                port=int(server['port']),
                username=server.get('username'),
                password=server.get('password'),
                rdns=True  # Force remote DNS resolution
            )
            
            # Patch socket for DNS resolution
            socks.wrap_module(socket)
            
            # Force DNS resolution through proxy
            def getaddrinfo_proxy(*args, **kwargs):
                return socket.getaddrinfo(*args, **kwargs)
            
            socket.getaddrinfo = getaddrinfo_proxy
            
            return True
        except Exception as e:
            self.logger.error(f"Error setting up proxy: {str(e)}")
            return False

    def connect(self, server):
        """Connect to a VPN server"""
        if not isinstance(server, dict):
            self.logger.error("Invalid server configuration")
            self.status_changed.emit(False, "Invalid server configuration")
            return False

        self.logger.info(f"Connecting to {server['name']}...")

        try:
            # First test the SOCKS5 connection with a shorter timeout
            if not self._test_socks_connection(server['host'], server['port'], timeout=5):
                self.logger.error("Failed to establish SOCKS5 connection")
                self.status_changed.emit(False, "Failed to connect to VPN server")
                return False

            # Set up proxy
            self._setup_proxy(server)
            
            # Create new session with proxy
            self.session = self._create_session(server['host'], server['port'])

            # Test connection with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Set connection state
                    self.is_connected = True
                    self.current_server = server
                    
                    # Verify IP location
                    ip_info = self._get_current_ip()
                    if not ip_info:
                        raise Exception("Could not verify IP location")
                    
                    ip, city, country = ip_info
                    
                    # Verify we're in the right country
                    if country != "Unknown" and country != server['country']:
                        self.logger.error(f"VPN connection failed - wrong country: {country}")
                        self.disconnect()
                        self.status_changed.emit(False, f"Connection failed: Wrong country detected ({country})")
                        return False
                    
                    self.logger.info(f"Connected successfully!")
                    self.logger.info(f"New IP: {ip}")
                    self.logger.info(f"Location: {city}, {country}")
                    self.status_changed.emit(True, f"Connected to {server['name']}")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Shorter delay between retries
                    continue

            self.logger.error("All connection attempts failed")
            self.disconnect()
            self.status_changed.emit(False, "All connection attempts failed")
            return False

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.disconnect()
            self.status_changed.emit(False, f"Connection failed: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from VPN"""
        # Restore original socket and DNS resolver
        if self.original_socket:
            socket.socket = self.original_socket
        if self.original_getaddrinfo:
            socket.getaddrinfo = self.original_getaddrinfo
            
        # Close and clear session
        if self.session:
            self.session.close()
            self.session = None
            
        self.is_connected = False
        self.current_server = None
        self.logger.info("Disconnected from VPN")
        self.status_changed.emit(False, "Disconnected")

    def get_status(self) -> tuple:
        """Get current VPN status"""
        if self.is_connected and self.current_server:
            ip_info = self._get_current_ip()
            if ip_info:
                return True, f"Connected to {self.current_server['name']} ({ip_info[0]})"
        return False, "Not connected"

    def get_ip_info(self):
        """Get IP and location information"""
        try:
            # Try m