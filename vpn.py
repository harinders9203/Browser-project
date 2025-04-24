import os
import sys
import json
import random
import socket
import logging
import argparse
import subprocess
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("vpn_client.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("VPN-Client")

class VPNClient:
    """A VPN client that can connect to servers in multiple countries to hide your IP."""
    
    def __init__(self, config_path: str = "vpn_config.json"):
        """Initialize the VPN client."""
        self.config_path = config_path
        self.config = self._load_config()
        self.current_connection = None
        self.original_ip = self._get_current_ip()
        logger.info(f"Original IP: {self.original_ip}")
        
    def _load_config(self) -> Dict:
        """Load VPN configuration from a JSON file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                # Create a default configuration
                default_config = {
                    "servers": {
                        "usa": {
                            "host": "vpn-usa.example.com",
                            "port": 1194,
                            "protocol": "udp",
                            "username": "",
                            "password": ""
                        },
                        "germany": {
                            "host": "vpn-de.example.com",
                            "port": 1194,
                            "protocol": "udp",
                            "username": "",
                            "password": ""
                        },
                        "japan": {
                            "host": "vpn-jp.example.com",
                            "port": 1194,
                            "protocol": "udp",
                            "username": "",
                            "password": ""
                        }
                    },
                    "connection_timeout": 30,
                    "reconnect_attempts": 3,
                    "default_country": "usa"
                }
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default configuration at {self.config_path}")
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            sys.exit(1)
    
    def _get_current_ip(self) -> str:
        """Get the current public IP address."""
        try:
            # Using a reliable service to get the public IP
            # In a real implementation, you might want to use multiple services for redundancy
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("ifconfig.me", 80))
                s.sendall(b"GET / HTTP/1.1\r\nHost: ifconfig.me\r\n\r\n")
                response = b""
                while True:
                    data = s.recv(1024)
                    if not data:
                        break
                    response += data
                
                # Parse the response to get just the IP
                return response.decode().split("\r\n\r\n")[1].strip()
        except Exception as e:
            logger.error(f"Error getting current IP: {str(e)}")
            return "Unknown"
    
    def list_available_countries(self) -> List[str]:
        """List all available countries to connect to."""
        return list(self.config["servers"].keys())
    
    def connect(self, country: Optional[str] = None) -> bool:
        """Connect to a VPN server in the specified country or a random one."""
        available_countries = self.list_available_countries()
        
        if not available_countries:
            logger.error("No VPN servers configured")
            return False
        
        if country is None:
            # Use default country or random if not specified
            country = self.config.get("default_country")
            if country not in available_countries:
                country = random.choice(available_countries)
                logger.info(f"Using random country: {country}")
        elif country not in available_countries:
            logger.error(f"Country '{country}' not available. Available countries: {', '.join(available_countries)}")
            return False
        
        server_config = self.config["servers"][country]
        logger.info(f"Connecting to VPN server in {country.upper()}: {server_config['host']}")
        
        # In a real implementation, this would use OpenVPN, WireGuard, or another VPN protocol
        # For this example, we'll simulate a connection
        
        try:
            # Simulate VPN connection process
            logger.info(f"Establishing connection to {server_config['host']}:{server_config['port']}...")
            
            # In a real implementation, you would run something like:
            # subprocess.run([
            #     "openvpn", 
            #     "--config", f"{country}.ovpn",
            #     "--daemon"
            # ], check=True)
            
            # For simulation, we'll just wait a bit
            import time
            time.sleep(2)
            
            # Store connection details
            self.current_connection = {
                "country": country,
                "server": server_config["host"],
                "connected_at": datetime.now().isoformat(),
                "virtual_ip": f"10.8.{random.randint(0, 255)}.{random.randint(1, 254)}"
            }
            
            new_ip = self._get_current_ip()
            logger.info(f"Connected! New IP: {new_ip}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to VPN: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from the current VPN connection."""
        if not self.current_connection:
            logger.warning("No active VPN connection")
            return False
        
        try:
            logger.info(f"Disconnecting from {self.current_connection['country'].upper()}...")
            
            # In a real implementation, you would run something like:
            # subprocess.run(["pkill", "openvpn"], check=True)
            
            # For simulation, we'll just wait a bit
            import time
            time.sleep(1)
            
            logger.info(f"Disconnected from {self.current_connection['country'].upper()}")
            self.current_connection = None
            
            current_ip = self._get_current_ip()
            logger.info(f"Current IP after disconnect: {current_ip}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from VPN: {str(e)}")
            return False
    
    def reconnect(self, country: Optional[str] = None) -> bool:
        """Reconnect to a VPN server, optionally changing the country."""
        self.disconnect()
        return self.connect(country)
    
    def connection_status(self) -> Dict:
        """Get the current connection status."""
        if not self.current_connection:
            return {"status": "disconnected", "original_ip": self.original_ip}
        
        return {
            "status": "connected",
            "country": self.current_connection["country"],
            "server": self.current_connection["server"],
            "connected_at": self.current_connection["connected_at"],
            "virtual_ip": self.current_connection["virtual_ip"],
            "public_ip": self._get_current_ip(),
            "original_ip": self.original_ip
        }
    
    def test_connection_speed(self) -> Dict:
        """Test the current connection speed."""
        # In a real implementation, this would use a speed test library or service
        import random
        
        if not self.current_connection:
            logger.warning("No active VPN connection to test")
            return {"error": "Not connected to VPN"}
        
        try:
            # Simulate a speed test
            download_speed = random.uniform(5.0, 50.0)  # Mbps
            upload_speed = random.uniform(1.0, 10.0)    # Mbps
            ping = random.uniform(20.0, 150.0)          # ms
            
            result = {
                "download_speed": round(download_speed, 2),
                "upload_speed": round(upload_speed, 2),
                "ping": round(ping, 2),
                "country": self.current_connection["country"],
                "server": self.current_connection["server"],
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Speed test results: {download_speed:.2f} Mbps down, {upload_speed:.2f} Mbps up, {ping:.2f} ms ping")
            return result
            
        except Exception as e:
            logger.error(f"Failed to test connection speed: {str(e)}")
            return {"error": str(e)}
    
    def check_ip_leaks(self) -> Dict:
        """Check for potential IP leaks (DNS, WebRTC, etc.)."""
        # In a real implementation, this would check various leak vectors
        try:
            # Simulate leak checks
            dns_leak = random.random() < 0.1  # 10% chance of a simulated leak
            webrtc_leak = random.random() < 0.05  # 5% chance of a simulated leak
            
            result = {
                "dns_leak_detected": dns_leak,
                "webrtc_leak_detected": webrtc_leak,
                "timestamp": datetime.now().isoformat()
            }
            
            if dns_leak or webrtc_leak:
                logger.warning(f"Potential IP leaks detected: {result}")
            else:
                logger.info("No IP leaks detected")
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to check for IP leaks: {str(e)}")
            return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Multi-Country VPN Client")
    parser.add_argument("--config", type=str, default="vpn_config.json", help="Path to configuration file")
    parser.add_argument("--connect", type=str, help="Connect to a specific country")
    parser.add_argument("--disconnect", action="store_true", help="Disconnect from current VPN")
    parser.add_argument("--status", action="store_true", help="Show current connection status")
    parser.add_argument("--list", action="store_true", help="List available countries")
    parser.add_argument("--speed", action="store_true", help="Test connection speed")
    parser.add_argument("--check-leaks", action="store_true", help="Check for IP leaks")
    args = parser.parse_args()
    
    client = VPNClient(args.config)
    
    if args.list:
        countries = client.list_available_countries()
        print(f"Available countries: {', '.join(countries)}")
    
    elif args.connect:
        client.connect(args.connect)
    
    elif args.disconnect:
        client.disconnect()
    
    elif args.status:
        status = client.connection_status()
        print(json.dumps(status, indent=2))
    
    elif args.speed:
        result = client.test_connection_speed()
        print(json.dumps(result, indent=2))
    
    elif args.check_leaks:
        result = client.check_ip_leaks()
        print(json.dumps(result, indent=2))
    
    else:
        # Interactive mode
        print("VPN Client - Interactive Mode")
        print("Type 'help' for available commands")
        
        while True:
            command = input("> ").strip().lower()
            
            if command == "help":
                print("Available commands:")
                print("  connect [country] - Connect to a VPN server")
                print("  disconnect - Disconnect from current VPN")
                print("  status - Show current connection status")
                print("  list - List available countries")
                print("  speed - Test connection speed")
                print("  check - Check for IP leaks")
                print("  exit/quit - Exit the program")
            
            elif command.startswith("connect"):
                parts = command.split()
                country = parts[1] if len(parts) > 1 else None
                client.connect(country)
            
            elif command == "disconnect":
                client.disconnect()
            
            elif command == "status":
                status = client.connection_status()
                print(json.dumps(status, indent=2))
            
            elif command == "list":
                countries = client.list_available_countries()
                print(f"Available countries: {', '.join(countries)}")
            
            elif command == "speed":
                result = client.test_connection_speed()
                print(json.dumps(result, indent=2))
            
            elif command == "check":
                result = client.check_ip_leaks()
                print(json.dumps(result, indent=2))
            
            elif command in ["exit", "quit"]:
                if client.current_connection:
                    print("Disconnecting from VPN before exit...")
                    client.disconnect()
                print("Goodbye!")
                break
            
            else:
                print("Unknown command. Type 'help' for available commands.")

if __name__ == "__main__":
    main()