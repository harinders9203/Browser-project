# dark_mode.py
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QWidget, QApplication, QMenu
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt
from vpn_handler import VPNHandler

class DarkModeManager:
    def __init__(self, parent, servo_thread, tabs_dict, tabs, new_tab_button):
        super().__init__()
        self.parent = parent
        self.servo_thread = servo_thread
        self.tabs_dict = tabs_dict
        self.tabs = tabs
        self.new_tab_button = new_tab_button
        self.dark_mode = False
        
        # Initialize VPN handler
        self.vpn_handler = VPNHandler()
        self.vpn_handler.status_changed.connect(self.on_vpn_status_changed)

        # Create toolbar for the dark mode and VPN buttons
        self.toolbar = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 0)
        
        # Initialize the dark mode button with an icon
        self.dark_mode_button = QPushButton()
        self.dark_mode_button.setText("Dark Mode: Off")
        try:
            self.dark_mode_button.setIcon(QIcon("dark_mode_icon.png"))
        except Exception as e:
            print(f"Warning: Could not load dark mode icon: {e}")
        self.dark_mode_button.setIconSize(QSize(24, 24))
        self.dark_mode_button.setFixedSize(250, 50)
        self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
        toolbar_layout.addWidget(self.dark_mode_button)

        # Initialize the VPN button with context menu
        self.vpn_button = QPushButton()
        self.vpn_button.setText("VPN: Checking...")
        try:
            self.vpn_button.setIcon(QIcon("vpn_icon.png"))
        except Exception as e:
            print(f"Warning: Could not load VPN icon: {e}")
        self.vpn_button.setIconSize(QSize(24, 24))
        self.vpn_button.setFixedSize(250, 50)
        self.vpn_button.clicked.connect(self.toggle_vpn)
        self.vpn_button.setObjectName("vpnButton")
        
        # Create VPN context menu
        self.vpn_menu = QMenu(self.vpn_button)
        self.vpn_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.vpn_button.customContextMenuRequested.connect(self.show_vpn_menu)
        toolbar_layout.addWidget(self.vpn_button)

        # Add Change Background button
        self.bg_button = QPushButton()
        self.bg_button.setText("🖼️ Change Background")
        self.bg_button.setIconSize(QSize(24, 24))
        self.bg_button.setFixedSize(250, 50)
        self.bg_button.clicked.connect(self.change_background)
        self.bg_button.setObjectName("bgButton")
        toolbar_layout.addWidget(self.bg_button)
        
        toolbar_layout.addStretch()
        self.toolbar.setLayout(toolbar_layout)

        # Initial styling
        self.update_application_style()

    def get_toolbar(self):
        return self.toolbar

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.servo_thread.set_dark_mode(self.dark_mode)
        self.dark_mode_button.setText(f"Dark Mode: {'On' if self.dark_mode else 'Off'}")
        
        # Update the entire application's style
        self.update_application_style()
        
        # Update all tabs' URL bar styles and reload content safely
        for tab_id, tab in self.tabs_dict.items():
            try:
                tab.update_url_bar_style(self.dark_mode)
                tab.apply_dark_mode_to_content(self.dark_mode)
                if hasattr(tab, 'current_url') and tab.current_url:
                    tab.handle_input()
            except AttributeError as e:
                print(f"Error updating tab {tab_id}: {e}")

    def show_vpn_menu(self, pos):
        """Show VPN server selection menu."""
        self.vpn_menu.clear()  # Clear existing items
        
        # Add server options
        for i, server in enumerate(self.vpn_handler.servers):
            action = self.vpn_menu.addAction(f"{server['name']} ({server['country']})")
            action.triggered.connect(lambda checked, idx=i: self.connect_to_vpn_server(idx))
        
        # Show the menu
        self.vpn_menu.exec_(self.vpn_button.mapToGlobal(pos))

    def toggle_vpn(self):
        """Toggle VPN connection on/off."""
        self.vpn_button.setEnabled(False)
        self.vpn_button.setText("VPN: Please wait...")
        self.vpn_handler.toggle_connection()

    def connect_to_vpn_server(self, server_index):
        """Connect to a specific VPN server."""
        self.vpn_button.setEnabled(False)
        self.vpn_button.setText("VPN: Connecting...")
        self.vpn_handler.connect(server_index)

    def on_vpn_status_changed(self, is_connected, message):
        """Handle VPN status changes."""
        self.vpn_button.setEnabled(True)
        if is_connected:
            self.vpn_button.setText("VPN: On")
            self.vpn_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50 !important;
                    color: white !important;
                    border: none !important;
                }
                QPushButton:hover {
                    background-color: #45a049 !important;
                }
            """)
        else:
            self.vpn_button.setText("VPN: Off")
            self.vpn_button.setStyleSheet("")  # Reset to default style
        
        # Show status message
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(None, "VPN Status", message)
        
        # Update the browser's VPN status
        self.servo_thread.set_vpn(is_connected)

    def update_application_style(self):
        if self.dark_mode:
            app_style = """
                QMainWindow {
                    background-color: #212121;
                }
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-radius: 10px;
                    padding: 8px;
                    spacing: 15px;
                }
                QMenuBar::item {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-radius: 10px;
                    margin: 2px 10px;
                    padding: 8px 15px;
                }
                QMenuBar::item:selected {
                    background-color: #3f3f3f;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #424242;
                    border-radius: 10px;
                }
                QMenu::item {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-radius: 8px;
                    padding: 5px 15px;
                }
                QMenu::item:selected {
                    background-color: #3f3f3f;
                }
                QWidget#toolbar {
                    background-color: #212121;
                    border-radius: 15px;
                    margin: 5px;
                }
                QPushButton#darkModeButton, QPushButton#vpnButton, QPushButton#bgButton {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #424242;
                    border-radius: 15px;
                    padding: 8px 15px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton#darkModeButton:hover, QPushButton#vpnButton:hover, QPushButton#bgButton:hover {
                    background-color: #3f3f3f;
                    border: 1px solid #ff9500;
                }
                QTabBar::tab { 
                    height: 35px; 
                    min-width: 150px; 
                    padding: 5px 20px 5px 30px;
                    font-size: 14px; 
                    font-weight: 500; 
                    background-color: #2d2d2d; 
                    color: #e0e0e0; 
                    border: 1px solid #424242; 
                    border-bottom: none; 
                    border-top-left-radius: 15px; 
                    border-top-right-radius: 15px; 
                    margin-right: 4px; 
                }
                QTabBar::tab:selected { 
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3f3f3f, stop:1 #2d2d2d); 
                    color: #ffffff; 
                    border-bottom: 2px solid #ff9500; 
                    border-top: 2px solid #ff9500; 
                }
                QTabBar::tab:hover:!selected {
                    background-color: #353535;
                }
                QTabBar::close-button {
                    image: url(close.png); 
                    subcontrol-position: right; 
                    margin-right: 4px;
                    width: 14px;
                    height: 14px;
                    border-radius: 7px;
                }
                QTabBar::close-button:hover {
                    background-color: #ff6d6d;
                    border-radius: 7px;
                }
                QProgressBar {
                    border: 1px solid #ff9500;
                    background: #2d2d2d;
                    text-align: center;
                    height: 24px;
                    width: 24px;
                    border-radius: 12px;
                }
                QProgressBar::chunk {
                    background-color: #ff9500;
                    width: 10px;
                    margin: 0.5px;
                    border-radius: 5px;
                }
                QTabWidget::pane { 
                    background-color: #212121; 
                    border-top: 1px solid #424242;
                    border-radius: 15px;
                }
                QToolButton#newTabButton {
                    font-size: 16px; 
                    padding: 8px; 
                    background-color: #2d2d2d; 
                    color: #e0e0e0; 
                    border: none;
                    border-radius: 12px;
                    margin: 2px;
                }
                QToolButton#newTabButton:hover {
                    background-color: #3f3f3f;
                }
            """
        else:
            app_style = """
                QMainWindow {
                    background-color: #ffffff;
                }
                QMenuBar {
                    background-color: #f5f5f5;
                    color: #333333;
                    border-radius: 10px;
                    padding: 8px;
                    spacing: 15px;
                }
                QMenuBar::item {
                    background-color: #f5f5f5;
                    color: #333333;
                    border-radius: 10px;
                    margin: 2px 10px;
                    padding: 8px 15px;
                }
                QMenuBar::item:selected {
                    background-color: #e0e0e0;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #d0d0d0;
                    border-radius: 10px;
                }
                QMenu::item {
                    background-color: #ffffff;
                    color: #333333;
                    border-radius: 8px;
                    padding: 5px 15px;
                }
                QMenu::item:selected {
                    background-color: #e0e0e0;
                }
                QWidget#toolbar {
                    background-color: #ffffff;
                    border-radius: 15px;
                    margin: 5px;
                }
                QPushButton#darkModeButton, QPushButton#vpnButton, QPushButton#bgButton {
                    background-color: #f5f5f5;
                    color: #333333;
                    border: 1px solid #d0d0d0;
                    border-radius: 15px;
                    padding: 8px 15px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton#darkModeButton:hover, QPushButton#vpnButton:hover, QPushButton#bgButton:hover {
                    background-color: #e0e0e0;
                    border: 1px solid #007bff;
                }
                QTabBar::tab { 
                    height: 35px;
                    min-width: 150px;
                    padding: 5px 20px 5px 30px;
                    font-size: 14px; 
                    font-weight: 500; 
                    background-color: #f5f5f5; 
                    color: #333333; 
                    border: 1px solid #d0d0d0; 
                    border-bottom: none; 
                    border-top-left-radius: 15px; 
                    border-top-right-radius: 15px; 
                    margin-right: 4px; 
                }
                QTabBar::tab:selected { 
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f5f5f5); 
                    color: #007bff; 
                    border-bottom: 2px solid #007bff; 
                    border-top: 2px solid #007bff; 
                }
                QTabBar::tab:hover:!selected {
                    background-color: #e0e0e0;
                }
                QTabBar::close-button {
                    image: url(close.png); 
                    subcontrol-position: right; 
                    margin-right: 4px;
                    width: 14px;
                    height: 14px;
                    border-radius: 7px;
                }
                QTabBar::close-button:hover {
                    background-color: #ff6d6d;
                    border-radius: 7px;
                }
                QProgressBar {
                    border: 1px solid #007bff;
                    background: #f5f5f5;
                    text-align: center;
                    height: 24px;
                    width: 24px;
                    border-radius: 12px;
                }
                QProgressBar::chunk {
                    background-color: #007bff;
                    width: 10px;
                    margin: 0.5px;
                    border-radius: 5px;
                }
                QTabWidget::pane { 
                    background-color: #ffffff; 
                    border-top: 1px solid #d0d0d0;
                    border-radius: 15px;
                }
                QToolButton#newTabButton {
                    font-size: 16px; 
                    padding: 8px;
                    background-color: #f5f5f5; 
                    color: #333333; 
                    border: none;
                    border-radius: 12px;
                    margin: 2px;
                }
                QToolButton#newTabButton:hover {
                    background-color: #e0e0e0;
                }
            """
        
        # Apply the stylesheet to the entire application safely
        try:
            QApplication.instance().setStyleSheet(app_style)
        except Exception as e:
            print(f"Error applying stylesheet: {e}")
        
        # Set object names for specific widgets to apply styles
        self.toolbar.setObjectName("toolbar")
        self.dark_mode_button.setObjectName("darkModeButton")
        self.vpn_button.setObjectName("vpnButton")
        self.new_tab_button.setObjectName("newTabButton")

    def get_content_css(self):
        if self.dark_mode:
            return """
                html, body {
                    background-color: #212121 !important;
                    color: #e0e0e0 !important;
                }
                a {
                    color: #ff9500 !important;
                }
                a:hover {
                    text-decoration: underline !important;
                }
                input, textarea, select {
                    background-color: #2d2d2d !important;
                    color: #e0e0e0 !important;
                    border: 1px solid #424242 !important;
                }
                button {
                    background-color: #2d2d2d !important;
                    color: #e0e0e0 !important;
                    border: 1px solid #424242 !important;
                }
                button:hover {
                    background-color: #3f3f3f !important;
                }
                div, p, span, h1, h2, h3, h4, h5, h6 {
                    color: #e0e0e0 !important;
                    background-color: transparent !important;
                }
                * {
                    scrollbar-color: #424242 #212121 !important;
                }
                [style*="background"], [style*="background-color"] {
                    background-color: #212121 !important;
                }
                [style*="color"] {
                    color: #e0e0e0 !important;
                }
            """
        return ""

    def is_dark_mode(self):
        return self.dark_mode

    def change_background(self):
        if hasattr(self.parent, 'add_image'):
            current_tab = None
            if self.tabs:
                current_tab = self.tabs.currentWidget()
            self.parent.add_image(current_tab)