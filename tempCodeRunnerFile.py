        def __init__(self):
            super().__init__()
            self.setWindowTitle("Servo Web Browser")
            self.setGeometry(300, 100, 1200, 800)

            # Start Servo Thread
            self.servo_thread = ServoThread(self)
            self.servo_thread.content_ready.connect(self.update_tab_content)
            self.servo_thread.start()
            
            # Tab counter for unique IDs
            self.tab_counter = 0
            self.tabs_dict = {}
            
            # Main Widget
            self.main_widget = QWidget()
            self.layout = QVBoxLayout()
            
            # Tab Widget
            self.tabs = QTabWidget()
            self.tabs.setTabsClosable(True)
            self.tabs.tabCloseRequested.connect(self.close_tab)
            
            # Add + button for new tab
            self.new_tab_button = QToolButton()
            self.new_tab_button.setText("+")
            self.new_tab_button.clicked.connect(lambda: self.add_new_tab(""))
            self.tabs.setCornerWidget(self.new_tab_button, Qt.TopRightCorner)

            self.layout.addWidget(self.tabs)

            # Add initial tab - DuckDuckGo as homepage
            self.add_new_tab("https://duckduckgo.com/html")

            # Set layout and central widget
            self.main_widget.setLayout(self.layout)
            self.setCentralWidget(self.main_widget)

            # Force fallback for problematic sites by default
            self.force_fallback = True
            self.servo_thread.set_force_fallback(self.force_fallback)

            # Add menu actions
            self.create_menu()