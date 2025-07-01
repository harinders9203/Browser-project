# layout.py
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QTabWidget, QToolButton, QProgressBar, QTabBar, QHBoxLayout, QPushButton, QMessageBox, QSizePolicy
from PyQt5.QtCore import Qt
from vpn_handler import VPNHandler
from test_vpn import VPNWindow
import os
import subprocess

class BrowserLayout(QWidget):
    def __init__(self, parent, dark_mode_manager, servo_thread, tabs_dict, new_tab_button):
        super().__init__(parent)
        self.parent = parent
        self.dark_mode_manager = dark_mode_manager
        self.servo_thread = servo_thread
        self.tabs_dict = tabs_dict
        self.new_tab_button = new_tab_button
        self.vpn_handler = VPNHandler()
        self.loading_indicators = {}
        self.vpn_window = None

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Top controls layout
        top_controls = QHBoxLayout()
        top_controls.setSpacing(15)  # Equal spacing between all buttons
        top_controls.setContentsMargins(15, 8, 15, 8)  # Consistent margins
        
        # All buttons in a single row with equal spacing
        # Dark mode toggle
        self.dark_mode_button = QPushButton("Dark Mode: Off")
        self.dark_mode_button.setObjectName("controlButton")
        self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
        top_controls.addWidget(self.dark_mode_button)

        # VPN status
        self.vpn_status = QPushButton("VPN: Checking...")
        self.vpn_status.setObjectName("controlButton")
        self.vpn_status.clicked.connect(self.toggle_vpn)
        top_controls.addWidget(self.vpn_status)

        # Proxy button
        self.proxy_button = QPushButton("Proxy: Off")
        self.proxy_button.setObjectName("controlButton")
        self.proxy_button.clicked.connect(self.toggle_proxy)
        top_controls.addWidget(self.proxy_button)

        # Phishing Detection button
        self.phishing_button = QPushButton("Phishing Detection: On")
        self.phishing_button.setObjectName("controlButton")
        self.phishing_button.clicked.connect(self.toggle_phishing_detection)
        top_controls.addWidget(self.phishing_button)

        # Ad Blocker button
        self.ad_blocker_button = QPushButton("Ad Blocker: On")
        self.ad_blocker_button.setObjectName("controlButton")
        self.ad_blocker_button.clicked.connect(self.toggle_ad_blocker)
        top_controls.addWidget(self.ad_blocker_button)

        # Change background button
        self.bg_button = QPushButton("Change Background")
        self.bg_button.setObjectName("controlButton")
        self.bg_button.clicked.connect(lambda: self.parent.add_image(self.tabs.currentWidget()))
        top_controls.addWidget(self.bg_button)

        top_controls.addStretch()
        self.main_layout.addLayout(top_controls)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.parent.close_tab)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.main_layout.addWidget(self.tabs)

        # New tab button
        self.new_tab_button.setText("+")
        self.new_tab_button.clicked.connect(lambda: self.parent.add_new_tab(""))
        self.tabs.setCornerWidget(self.new_tab_button)

        # Set the layout
        self.setLayout(self.main_layout)
        
        # Apply initial styles
        self.update_button_style()
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def update_button_style(self):
        """Update the style of all buttons in the top controls"""
        dark_mode = self.dark_mode_manager.is_dark_mode() if self.dark_mode_manager else False

        # Base colors
        if dark_mode:
            bg_color = "#2d2d2d"
            text_color = "#ffffff"
            hover_bg = "#3d3d3d"
            pressed_bg = "#1d1d1d"
            border_color = "#404040"
        else:
            bg_color = "#f0f0f0"
            text_color = "#000000"
            hover_bg = "#e0e0e0"
            pressed_bg = "#d0d0d0"
            border_color = "#cccccc"

        style = f"""
            QPushButton#controlButton {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 8px 15px;
                min-width: 120px;
                font-family: "Times New Roman";
                font-size: 14px;
                font-weight: normal;
            }}
            
            QPushButton#controlButton:hover {{
                background-color: {hover_bg};
                border: 1px solid {border_color};
            }}
            
            QPushButton#controlButton:pressed {{
                background-color: {pressed_bg};
                border: 1px solid {border_color};
                padding: 9px 14px 7px 16px;  /* Shift content when pressed */
            }}
            
            QPushButton#controlButton:disabled {{
                background-color: {bg_color};
                color: {border_color};
                border: 1px solid {border_color};
            }}
        """
        
        # Apply the style to all control buttons
        self.setStyleSheet(style)

    def toggle_proxy(self):
        """Launch VPN client in a new terminal window"""
        try:
            vpn_script = os.path.join(os.getcwd(), "vpn_app.py")
            if os.name == 'nt':  # For Windows
                subprocess.Popen(
                    ['python', vpn_script],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:  # For Unix-like systems
                subprocess.Popen(['python3', vpn_script])
            
            # Update button state
            if "Enable" in self.proxy_button.text():
                self.proxy_button.setText("Disable Proxy")
                self.proxy_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #da190b;
                    }
                """)
            else:
                self.proxy_button.setText("Enable Proxy")
                self.proxy_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
        except Exception as e:
            print(f"Error launching VPN client: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to launch VPN client: {str(e)}")

    def toggle_dark_mode(self):
        """Toggle dark mode on/off"""
        if self.dark_mode_manager:
            self.dark_mode_manager.toggle_dark_mode()
            # Update the dark mode button text
            if hasattr(self, 'dark_mode_button'):
                self.dark_mode_button.setText(f"Dark Mode: {'On' if self.dark_mode_manager.is_dark_mode() else 'Off'}")
                self.dark_mode_button.setChecked(self.dark_mode_manager.is_dark_mode())

    def toggle_vpn(self):
        # Existing VPN toggle functionality
        pass

    def toggle_phishing_detection(self):
        """Toggle phishing detection and update button text"""
        if hasattr(self.parent, 'phishing_detection_enabled'):
            self.parent.phishing_detection_enabled = not self.parent.phishing_detection_enabled
            self.phishing_button.setText(f"Phishing Detection: {'On' if self.parent.phishing_detection_enabled else 'Off'}")
            
            # Show notification in current tab
            current_tab = self.tabs.currentWidget()
            if current_tab:
                notification_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Phishing Detection Status</title>
                    <style>
                        body {{ 
                            font-family: Arial, sans-serif; 
                            text-align: center; 
                            padding: 2%; 
                            font-size: 1.2em; 
                            background-color: { "#212121" if self.dark_mode_manager.is_dark_mode() else "#fff" }; 
                            color: { "#e0e0e0" if self.dark_mode_manager.is_dark_mode() else "#333" }; 
                        }}
                        .notification {{
                            background-color: { "#2d2d2d" if self.dark_mode_manager.is_dark_mode() else "#f0f8ff" };
                            padding: 20px;
                            border-radius: 10px;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                            margin: 100px auto;
                            max-width: 500px;
                        }}
                        .status-icon {{
                            font-size: 48px;
                            margin-bottom: 20px;
                        }}
                    </style>
                    <script>
                        setTimeout(function() {{
                            window.history.back();
                        }}, 2000);
                    </script>
                </head>
                <body>
                    <div class="notification">
                        <div class="status-icon">{'🛡️' if self.parent.phishing_detection_enabled else '🚫'}</div>
                        <h2>Phishing Detection {self.parent.phishing_detection_enabled and 'Enabled' or 'Disabled'}</h2>
                        <p>{'Protecting you from suspicious websites' if self.parent.phishing_detection_enabled else 'Protection is turned off'}</p>
                    </div>
                </body>
                </html>
                """
                current_tab.web_view.setHtml(notification_html)

    def toggle_ad_blocker(self):
        """Toggle ad blocker and update button text"""
        if hasattr(self.parent, 'ad_blocker_enabled'):
            self.parent.ad_blocker_enabled = not self.parent.ad_blocker_enabled
            self.parent.servo_thread.ad_blocker_enabled = self.parent.ad_blocker_enabled
            self.ad_blocker_button.setText(f"Ad Blocker: {'On' if self.parent.ad_blocker_enabled else 'Off'}")
            
            # Show notification in current tab
            current_tab = self.tabs.currentWidget()
            if current_tab:
                notification_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Ad Blocker Status</title>
                    <style>
                        body {{ 
                            font-family: Arial, sans-serif; 
                            text-align: center; 
                            padding: 2%; 
                            font-size: 1.2em; 
                            background-color: { "#212121" if self.dark_mode_manager.is_dark_mode() else "#fff" }; 
                            color: { "#e0e0e0" if self.dark_mode_manager.is_dark_mode() else "#333" }; 
                        }}
                        .notification {{
                            background-color: { "#2d2d2d" if self.dark_mode_manager.is_dark_mode() else "#f0f8ff" };
                            padding: 20px;
                            border-radius: 10px;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                            margin: 100px auto;
                            max-width: 500px;
                        }}
                        .status-icon {{
                            font-size: 48px;
                            margin-bottom: 20px;
                        }}
                    </style>
                    <script>
                        setTimeout(function() {{
                            window.history.back();
                        }}, 2000);
                    </script>
                </head>
                <body>
                    <div class="notification">
                        <div class="status-icon">{'🛡️' if self.parent.ad_blocker_enabled else '🚫'}</div>
                        <h2>Ad Blocker {self.parent.ad_blocker_enabled and 'Enabled' or 'Disabled'}</h2>
                        <p>{'Blocking ads and trackers' if self.parent.ad_blocker_enabled else 'Ad blocking is turned off'}</p>
                    </div>
                </body>
                </html>
                """
                current_tab.web_view.setHtml(notification_html)

    def add_tab(self, tab_widget, title):
        # Add the tab to the QTabWidget
        idx = self.tabs.addTab(tab_widget, title)
        self.tabs.setCurrentIndex(idx)

        # Create a loading indicator for this tab
        loading_indicator = QProgressBar()
        loading_indicator.setFixedSize(24, 24)  # Match the stylesheet size
        loading_indicator.setRange(0, 0)  # Indeterminate mode (spinning)
        loading_indicator.setVisible(False)  # Hidden by default
        self.loading_indicators[tab_widget.tab_id] = loading_indicator

        # Add the loading indicator to the tab bar
        self.tabs.tabBar().setTabButton(idx, QTabBar.LeftSide, loading_indicator)

    def show_loading(self, tab_id):
        if tab_id in self.loading_indicators:
            print(f"Showing loading indicator for tab_id: {tab_id}")
            self.loading_indicators[tab_id].setVisible(True)

    def hide_loading(self, tab_id):
        if tab_id in self.loading_indicators:
            print(f"Hiding loading indicator for tab_id: {tab_id}")
            self.loading_indicators[tab_id].setVisible(False)

    def get_tabs(self):
        return self.tabs