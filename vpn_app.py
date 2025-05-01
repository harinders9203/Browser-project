from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QComboBox, QMessageBox, QHBoxLayout,
                            QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from vpn_handler import VPNHandler
import sys

class VPNWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VPN Client")
        self.setMinimumSize(600, 400)
        
        # Create VPN handler
        self.vpn_handler = VPNHandler()
        self.vpn_handler.status_changed.connect(self.update_status)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("VPN Client")
        title_label.setFont(QFont('Arial', 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Status frame
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        status_layout = QVBoxLayout(status_frame)
        
        # Status label
        self.status_label = QLabel("Not connected")
        self.status_label.setFont(QFont('Arial', 12))
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        # Location info
        self.location_label = QLabel()
        self.location_label.setFont(QFont('Arial', 10))
        self.location_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.location_label)
        
        # IP Label
        self.ip_label = QLabel()
        self.ip_label.setFont(QFont('Arial', 10))
        self.ip_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.ip_label)
        
        layout.addWidget(status_frame)
        
        # Server selection frame
        server_frame = QFrame()
        server_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        server_layout = QVBoxLayout(server_frame)
        
        # Server selection label
        server_label = QLabel("Select Server:")
        server_label.setFont(QFont('Arial', 12))
        server_layout.addWidget(server_label)
        
        # Server selection
        self.server_combo = QComboBox()
        self.server_combo.setFont(QFont('Arial', 10))
        self.servers = list(self.vpn_handler.get_default_servers().values())
        for server in self.servers:
            self.server_combo.addItem(f"{server['name']} ({server['host']}:{server['port']})")
        server_layout.addWidget(self.server_combo)
        
        layout.addWidget(server_frame)
        
        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.connect_button.setMinimumHeight(50)
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button)
        
        # Add stretch to push everything up
        layout.addStretch()
        
        # Update initial status
        self.update_status(*self.vpn_handler.get_status())
        
        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QComboBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
            QLabel {
                color: #333333;
            }
        """)
    
    def toggle_connection(self):
        self.connect_button.setEnabled(False)
        self.server_combo.setEnabled(False)
        
        if self.vpn_handler.is_connected:
            self.vpn_handler.disconnect()
            self.location_label.setText("")
            self.ip_label.setText("")
            self.connect_button.setEnabled(True)
            self.server_combo.setEnabled(True)
        else:
            try:
                # Get the selected server configuration
                server = self.servers[self.server_combo.currentIndex()]
                if self.vpn_handler.connect(server):
                    ip_info = self.vpn_handler.get_ip_info()
                    if ip_info:
                        self.location_label.setText(f"Location: {ip_info.get('city', '')}, {ip_info.get('country', '')}")
                        self.ip_label.setText(f"IP: {ip_info.get('ip', '')}")
                else:
                    QMessageBox.warning(self, "Connection Failed", 
                                     "Failed to connect to the selected server. Please try another server.")
                    self.connect_button.setEnabled(True)
                    self.server_combo.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Connection error: {str(e)}")
                self.connect_button.setEnabled(True)
                self.server_combo.setEnabled(True)
    
    def update_status(self, is_connected, message):
        self.status_label.setText(message)
        self.connect_button.setText("Disconnect" if is_connected else "Connect")
        self.connect_button.setEnabled(True)
        self.server_combo.setEnabled(not is_connected)
        
        # Update button style based on connection status
        if is_connected:
            self.connect_button.setStyleSheet("""
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            """)
        else:
            self.connect_button.setStyleSheet("""
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            """)

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')

    window = VPNWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()