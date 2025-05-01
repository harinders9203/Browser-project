from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from vpn_handler import VPNHandler

class VPNThread(QThread):
    status_update = pyqtSignal(str)
    connection_success = pyqtSignal()
    connection_failed = pyqtSignal(str)
    
    def __init__(self, vpn_handler):
        super().__init__()
        self.vpn_handler = vpn_handler
        self.action = None  # 'connect' or 'disconnect'
        
    def set_action(self, action):
        self.action = action
        
    def run(self):
        try:
            if self.action == 'connect':
                self.status_update.emit("Connecting to VPN...")
                success = self.vpn_handler.connect()
                if success:
                    self.connection_success.emit()
                else:
                    self.connection_failed.emit("Failed to connect to VPN")
            elif self.action == 'disconnect':
                self.status_update.emit("Disconnecting from VPN...")
                self.vpn_handler.disconnect()
                self.status_update.emit("Disconnected from VPN")
        except Exception as e:
            self.connection_failed.emit(str(e))

class VPNWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.vpn_handler = VPNHandler()
        self.vpn_thread = VPNThread(self.vpn_handler)
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        self.setWindowTitle("VPN Control")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Status section
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #f44336;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        status_layout.addWidget(self.status_label)
        layout.addLayout(status_layout)
        
        # Server selection
        server_layout = QHBoxLayout()
        server_label = QLabel("Server:")
        self.server_combo = QComboBox()
        self.server_combo.addItems([
            "US Elite 1 (67.201.39.14:4145)",
            "US Elite 2 (199.102.104.70:4145)",
            "Singapore Elite (8.215.15.163:4145)"
        ])
        server_layout.addWidget(server_label)
        server_layout.addWidget(self.server_combo)
        layout.addLayout(server_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.connect_button)
        
        # Add some spacing
        layout.addStretch()
        
        self.setLayout(layout)
        
    def setup_connections(self):
        self.connect_button.clicked.connect(self.toggle_connection)
        self.vpn_thread.status_update.connect(self.update_status)
        self.vpn_thread.connection_success.connect(self.handle_connection_success)
        self.vpn_thread.connection_failed.connect(self.handle_connection_failure)
        
    def toggle_connection(self):
        if self.connect_button.text() == "Connect":
            self.start_connection()
        else:
            self.stop_connection()
            
    def start_connection(self):
        self.connect_button.setEnabled(False)
        self.progress_bar.setMaximum(0)
        self.progress_bar.show()
        self.vpn_thread.set_action('connect')
        self.vpn_thread.start()
        
    def stop_connection(self):
        self.connect_button.setEnabled(False)
        self.progress_bar.setMaximum(0)
        self.progress_bar.show()
        self.vpn_thread.set_action('disconnect')
        self.vpn_thread.start()
        
    def update_status(self, message):
        self.status_label.setText(f"Status: {message}")
        
    def handle_connection_success(self):
        self.progress_bar.hide()
        self.connect_button.setEnabled(True)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        self.status_label.setText("Status: Connected")
        self.connect_button.setText("Disconnect")
        self.connect_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
    def handle_connection_failure(self, error_message):
        self.progress_bar.hide()
        self.connect_button.setEnabled(True)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #f44336;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        self.status_label.setText("Status: Disconnected")
        self.connect_button.setText("Connect")
        self.connect_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        QMessageBox.critical(self, "Connection Error", error_message)
        
    def closeEvent(self, event):
        if self.vpn_thread.isRunning():
            self.vpn_thread.set_action('disconnect')
            self.vpn_thread.wait()
        event.accept() 