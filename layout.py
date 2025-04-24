# layout.py
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QTabWidget, QToolButton, QProgressBar, QTabBar
from PyQt5.QtCore import Qt

class BrowserLayout(QWidget):
    def __init__(self, parent, dark_mode_manager, servo_thread, tabs_dict, new_tab_button):
        super().__init__(parent)
        self.parent = parent  # CustomWebRenderer instance
        self.dark_mode_manager = dark_mode_manager
        self.servo_thread = servo_thread
        self.tabs_dict = tabs_dict
        self.new_tab_button = new_tab_button
        self.loading_indicators = {}  # Track loading indicators for each tab

        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Add the toolbar (with dark mode button)
        self.toolbar = self.dark_mode_manager.get_toolbar()
        self.main_layout.addWidget(self.toolbar)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.parent.close_tab)

        # New tab button
        self.new_tab_button.setText("+")
        self.new_tab_button.clicked.connect(lambda: self.parent.add_new_tab(""))
        self.tabs.setCornerWidget(self.new_tab_button, Qt.TopRightCorner)

        self.main_layout.addWidget(self.tabs)
        self.setLayout(self.main_layout)

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