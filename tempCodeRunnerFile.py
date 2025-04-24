                debug_info = f"""
                <details class="debug-info">
                    <summary>Debug Info</summary>
                    <p><strong>URL:</strong> {response.url}</p>
                    <p><strong>Status:</strong> {response.status_code}</p>
                    <p><strong>Content-Type:</strong> {response.headers.get('Content-Type', 'Unknown')}</p>
                    <p><strong>Encoding:</strong> {response.encoding}</p>
                    <p><strong>User-Agent:</strong> {self.current_user_agent}</p>
                    <p><strong>VPN:</strong> {"On" if self.vpn_enabled else "Off"}</p>
                    <p><strong>Note:</strong> Using fallback HTML renderer</p>
                </details>
                """
                complete_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>{base_domain}</title>
                    {base_tag}
                    {custom_css}
                </head>
                <body>
                    {debug_info}
                    <div class="content">
                        {html_content}
                    </div>
                </body>
                </html>
                """
                temp_html = os.path.join(self.temp_dir, f"{tab_id}_fallback.html")
                with open(temp_html, 'w', encoding='utf-8', errors='replace') as f:
                    f.write(complete_html)
                print(f"Emitting fallback content: {temp_html}, length: {len(complete_html)}")
                time.sleep(0.5)
                self.content_ready.emit(temp_html, tab_id)
                self.loading_finished.emit(tab_id)
            else:
                print(f"Fetching URL with fallback: {url}")
                response = session.get(url, headers=headers, timeout=15)
                
                print(f"Response status code: {response.status_code}")
                content_type = response.headers.get('Content-Type', '').lower()
                if ('text/html' not in content_type and 
                    'application/json' not in content_type and 
                    'text/plain' not in content_type and
                    'application/javascript' not in content_type and
                    'text/xml' not in content_type):
                    html_content = f"""
                    <div style='padding: 2%; font-family: Arial; font-size: 1.2em; background-color: { "#2d2d2d" if self.dark_mode else "#fff" }; color: { "#e0e0e0" if self.dark_mode else "#333" };'>
                        <h2>Content type not supported</h2>
                        <p>The page at <a href="{url}">{url}</a> returned content of type: {content_type}</p>
                        <p>Try visiting the site in another browser.</p>
                    </div>
                    """
                else:
                    try:
                        html_content = response.content.decode('utf-8', errors='replace')
                        html_content = self._block_ads(html_content, url)
                    except Exception as e:
                        print(f"Error decoding content: {str(e)}")
                        html_content = response.text
                        html_content = self._block_ads(html_content, url)
                
                base_url = response.url
                base_domain = urllib.parse.urlparse(base_url).netloc
                base_tag = f'<base href="{base_url}">'
                dark_mode_css = self.dark_mode_manager.get_content_css() if self.dark_mode_manager else ""
                custom_css = f"""
                <style>
                    html, body {{ 
                        font-family: Arial, sans-serif; 
                        line-height: 1.6; 
                        color: { '#e0e0e0' if self.dark_mode else '#333' }; 
                        margin: 0;
                        padding: 30px;
                        font-size: 22px; 
                        background-color: { '#212121' if self.dark_mode else '#fff' }; 
                    }}
                    .search-container {{
                        max-width: 1000px;
                        margin: 0 auto;
                    }}
                    .search-result {{
                        background: { '#2d2d2d' if self.dark_mode else '#ffffff' };
                        padding: 25px;
                        margin-bottom: 30px;
                        border-radius: 16px;
                        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
                    }}
                    .result-title {{
                        font-size: 26px;
                        color: { '#ff9500' if self.dark_mode else '#1a0dab' };
                        margin-bottom: 15px;
                        text-decoration: none;
                        display: block;
                    }}
                    .result-url {{
                        font-size: 20px;
                        color: { '#888' if self.dark_mode else '#006621' };
                        margin-bottom: 15px;
                        word-break: break-all;
                    }}
                    .result-snippet {{
                        font-size: 22px;
                        line-height: 1.6;
                        color: { '#e0e0e0' if self.dark_mode else '#4d5156' };
                    }}
                    .search-filters {{
                        display: flex;
                        gap: 25px;
                        margin: 30px 0;
                        padding-bottom: 20px;
                        border-bottom: 2px solid { '#424242' if self.dark_mode else '#e0e0e0' };
                    }}
                    .search-filter {{
                        font-size: 22px;
                        color: { '#e0e0e0' if self.dark_mode else '#4d5156' };
                        text-decoration: none;
                        padding: 12px 24px;
                        border-radius: 25px;
                    }}
                    .search-filter.active {{
                        background: { '#424242' if self.dark_mode else '#e9e9e9' };
                        color: { '#fff' if self.dark_mode else '#000' };
                    }}
                    a {{ color: { '#ff9500' if self.dark_mode else '#1a0dab' }; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                    img {{ max-width: 100%; height: auto; border-radius: 8px; }}
                    {dark_mode_css}
                </style>
                """
                debug_info = f"""
                <details class="debug-info">
                    <summary>Debug Info</summary>
                    <p><strong>URL:</strong> {response.url}</p>
                    <p><strong>Status:</strong> {response.status_code}</p>
                    <p><strong>Content-Type:</strong> {response.headers.get('Content-Type', 'Unknown')}</p>
                    <p><strong>Encoding:</strong> {response.encoding}</p>
                    <p><strong>User-Agent:</strong> {self.current_user_agent}</p>
                    <p><strong>VPN:</strong> {"On" if self.vpn_enabled else "Off"}</p>
                    <p><strong>Note:</strong> Using fallback HTML renderer</p>
                </details>
                """
                complete_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>{base_domain}</title>
                    {base_tag}
                    {custom_css}
                </head>
                <body>
                    {debug_info}
                    <div class="content">
                        {html_content}
                    </div>
                </body>
                </html>
                """
                temp_html = os.path.join(self.temp_dir, f"{tab_id}_fallback.html")
                with open(temp_html, 'w', encoding='utf-8', errors='replace') as f:
                    f.write(complete_html)
                print(f"Emitting fallback content: {temp_html} for tab {tab_id}, length: {len(complete_html)}")
                time.sleep(0.5)
                self.content_ready.emit(temp_html, tab_id)
                self.loading_finished.emit(tab_id)
            
        except Exception as e:
            print(f"Fallback rendering error for {url}: {str(e)}")
            error_msg = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Error</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        padding: 2%; 
                        line-height: 1.6; 
                        font-size: 1.2em; 
                        background-color: { "#212121" if self.dark_mode else "#fff" }; 
                        color: { "#e0e0e0" if self.dark_mode else "#333" }; 
                    }}
                    .error-container {{ 
                        background-color: { "#2d2d2d" if self.dark_mode else "#fff3f3" }; 
                        border-left: 4px solid { "#ff6d6d" if self.dark_mode else "#e74c3c" }; 
                        padding: 2%; 
                        border-radius: 4px; 
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                    }}
                    h2 {{ margin-top: 0; color: { "#ff6d6d" if self.dark_mode else "#e74c3c" }; }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <h2>Error loading page</h2>
                    <p><strong>URL:</strong> {url}</p>
                    <p><strong>Error:</strong> {str(e)}</p>
                    <p>Both Servo rendering and fallback method failed.</p>
                    <p>Try reloading the page or checking your network connection.</p>
                </div>
            </body>
            </html>
            """
            temp_error = os.path.join(self.temp_dir, f"{tab_id}_error.html")
            with open(temp_error, 'w', encoding='utf-8') as f:
                f.write(error_msg)
            print(f"Emitting error content: {temp_error} for tab {tab_id}")
            self.content_ready.emit(temp_error, tab_id)
            self.loading_finished.emit(tab_id)
        finally:
            print(f"Emitting loading_finished signal for tab_id: {tab_id}")

    def _block_ads(self, html_content, base_url):
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for element in soup.find_all(['script', 'iframe', 'img', 'div', 'a']):
                src = element.get('src', '') or element.get('href', '') or ''
                if src and self._is_ad_url(src):
                    element.decompose()
                if any('ad' in str(val).lower() for val in element.get('class', []) + [element.get('id', '')]):
                    element.decompose()
            return str(soup)
        except Exception as e:
            print(f"Error blocking ads: {e}")
            return html_content

    def set_user_agent(self, ua_index):
        if 0 <= ua_index < len(self.user_agents):
            self.current_user_agent = self.user_agents[ua_index]

    def set_force_fallback(self, force):
        self.force_fallback = force

    def set_dark_mode(self, enabled):
        self.dark_mode = enabled

    def set_vpn(self, enabled):
        self.vpn_enabled = enabled
        print(f"ServoThread VPN set to: {'enabled' if enabled else 'disabled'}")

    def stop(self):
        self.running = False
        self.terminate()
        self.wait(2000)

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent_tab):
        super().__init__(parent_tab)
        self.parent_tab = parent_tab

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        url_str = url.toString()
        print(f"Navigation request: {url_str}, type: {navigation_type}, main_frame: {is_main_frame}")
        if url_str.startswith("about:") and is_main_frame:
            self.parent_tab.url_bar.setText(url_str)
            self.parent_tab.handle_input()
            return False
        return True

class BrowserTab(QWidget):
    def __init__(self, servo_thread, tab_id, url=None, dark_mode_manager=None, history_processor=None, parent_renderer=None):
        super().__init__()
        self.servo_thread = servo_thread
        self.tab_id = tab_id
        self.dark_mode_manager = dark_mode_manager
        self.history_processor = history_processor
        self.parent_renderer = parent_renderer
        self.layout = QVBoxLayout()
        self.default_search_engine = "https://duckduckgo.com/?t=h_&q={query}&ia=web"
        self.last_content_path = None
        self.update_lock = QMutex()
        self.handling_input = False
        self.content_loaded = False

        self.url_layout = QHBoxLayout()

        self.back_button = QPushButton("◄")
        self.back_button.setFixedSize(100, 100)
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setObjectName("backButton")
        self.url_layout.addWidget(self.back_button)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search query")
        self.url_bar.returnPressed.connect(self.handle_input)
        self.url_bar.setMinimumHeight(int(QApplication.primaryScreen().availableGeometry().height() * 0.05))
        self.url_layout.addWidget(self.url_bar)

        self.reload_button = QPushButton("↻")
        self.reload_button.setFixedSize(100, 100)
        self.reload_button.clicked.connect(self.handle_input)
        self.reload_button.setObjectName("reloadButton")
        self.url_layout.addWidget(self.reload_button)

        # Add background change button
        if url == "about:start":
            self.bg_button = QPushButton("🖼️")
            self.bg_button.setFixedSize(100, 100)
            self.bg_button.clicked.connect(self.change_background)
            self.bg_button.setObjectName("bgButton")
            self.bg_button.setToolTip("Change Background Image")
            self.url_layout.addWidget(self.bg_button)

        self.update_url_bar_style()

        self.layout.addLayout(self.url_layout)

        self.web_view = QWebEngineView()
        self.web_view.setPage(CustomWebEnginePage(self))
        self.web_view.loadFinished.connect(self.apply_dark_mode_to_content)
        self.layout.addWidget(self.web_view, 1)

        self.layout.setSpacing(10)
        self.setLayout(self.layout)

        self.current_url = ""
        if url:
            self.url_bar.setText(url)
            self.handle_input()

    def change_background(self):
        if self.parent_renderer:
            self.parent_renderer.add_image(self)

    def update_url_bar_style(self, dark_mode=False):
        if dark_mode:
            style = """ 
                padding: 8px; 
                font-size: 16px; 
                border: 1px solid #424242; 
                border-radius: 24px; 
                background-color: #2d2d2d; 
                color: #e0e0e0;
            """
            button_style = """
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #424242;
                border-radius: 20px;
                font-size: 18px;
            """
            button_hover = "background-color: #3f3f3f;"
        else:
            style = """
                padding: 8px; 
                font-size: 16px; 
                border: 1px solid #d0d0d0; 
                border-radius: 24px; 
                background-color: #fff; 
                color: #333;
            """
            button_style = """
                background-color: #f5f5f5;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 20px;
                font-size: 18px;
            """
            button_hover = "background-color: #e0e0e0;"

        self.url_bar.setStyleSheet(style)
        
        for button, name in [(self.back_button, "backButton"), 
                           (self.reload_button, "reloadButton"),
                           (getattr(self, 'bg_button', None), "bgButton")]:
            if button:
                button.setStyleSheet(f"""
                    QPushButton#{name} {{
                        {button_style}
                    }}
                    QPushButton#{name}:hover {{
                        {button_hover}
                    }}
                """)

    def apply_dark_mode_to_content(self, ok):
        if not self.update_lock.tryLock():
            print("Dark mode application skipped due to lock")
            return
        try:
            if self.dark_mode_manager:
                dark_mode = self.dark_mode_manager.is_dark_mode()
                css = self.dark_mode_manager.get_content_css()
                if css:
                    script = f"""
                        (function() {{
                            var style = document.createElement('style');
                            style.type = 'text/css';
                            style.innerHTML = `{css}`;
                            document.head.appendChild(style);
                            var ads = document.querySelectorAll('iframe[src*="ads"], script[src*="ads"], div[class*="ad"], div[id*="ad"]');
                            ads.forEach(ad => ad.remove());
                            console.log('Dark mode CSS applied and ads blocked');
                        }})();
                    """
                    self.web_view.page().runJavaScript(script)
        finally:
            self.update_lock.unlock()

    def is_url(self, text):
        text = text.lower().strip()
        if text.startswith(('http://', 'https://')):
            return True
        common_domains = ['.com', '.org', '.net', '.edu', '.gov', '.io', '.co', '.uk', '.de', '.jp', '.ru']
        if any(domain in text for domain in common_domains) and ' ' not in text:
            return True
        if '.' in text and ' ' not in text and not text.endswith('.'):
            return True
        common_sites = ['google', 'facebook', 'youtube', 'amazon', 'wikipedia', 'twitter', 'instagram']
        if any(site == text for site in common_sites):
            return True
        return False

    def handle_input(self):
        if self.handling_input:
            print("Recursive handle_input call detected, skipping")
            return
        
        self.handling_input = True
        try:
            input_text = self.url_bar.text().strip()
            
            # Skip if input is empty or unchanged
            if not input_text or (input_text == self.current_url and self.content_loaded):
                print("Skipping input - empty or unchanged")
                return

            # Special handling for about: pages
            if input_text.startswith("about:"):
                if input_text == self.current_url and self.content_loaded:
                    print("Skipping reload of about: page")
                    return
                    
            if input_text == "about:add-shortcut" and self.parent_renderer:
                print("Processing about:add-shortcut")
                self.parent_renderer.add_shortcut(self)
                return
            elif input_text == "about:add-image" and self.parent_renderer:
                print("Processing about:add-image")
                self.parent_renderer.add_image(self)
                return
            elif input_text == "about:start":
                print("Processing about:start")
                self.current_url = input_text
                self.url_bar.setText(input_text)
                if self.parent_renderer:
                    temp_html = self.parent_renderer.generate_starting_screen_html()
                    self.update_content(temp_html)
                return
            
            if self.is_url(input_text):
                if input_text.startswith('http://'):
                    url = 'https://' + input_text[7:]
                elif not input_text.startswith('https://'):
                    common_sites = ['google', 'facebook', 'youtube', 'amazon', 'wikipedia', 'twitter', 'instagram']
                    input_lower = input_text.lower()
                    if any(site == input_lower for site in common_sites):
                        url = f"https://www.{input_text}.com"
                    else:
                        url = "https://" + input_text
                else:
                    url = input_text
            else:
                encoded_query = urllib.parse.quote(input_text)
                url = self.default_search_engine.format(query=encoded_query)

            self.current_url = url
            self.url_bar.setText(url)
            self.last_content_path = None

            if self.history_processor and url and url != "about:start":
                title = urllib.parse.urlparse(url).netloc or "New Tab"
                self.history_processor.record_visit(url, title)

            old_fallback = self.servo_thread.force_fallback
            self.servo_thread.set_force_fallback(True)
            self.servo_thread.add_url_to_queue(url, self.tab_id)
            self.servo_thread.set_force_fallback(old_fallback)
        except Exception as e:
            print(f"Error handling input: {e}")
        finally:
            self.handling_input = False
            print("Finished handling input")

    def go_back(self):
        self.web_view.back()

    def update_content(self, content_path):
        if not content_path:
            return "Error"

        print(f"Attempting to load content into web view: {content_path}")
        if not self.update_lock.tryLock():
            print(f"Update locked, skipping content load for: {content_path}")
            return self._extract_title_from_path(content_path) or "Update Skipped"

        try:
            # Skip update if content hasn't changed
            if self.last_content_path == content_path and self.content_loaded:
                print("Skipping update - content unchanged")
                return self._extract_title_from_path(content_path) or "Same Content"

            if content_path.endswith(('.html', '.htm')):
                try:
                    file_url = QUrl.fromLocalFile(content_path)
                    with open(content_path, 'r', encoding='utf-8', errors='replace') as f:
                        html_content = f.read()
                        title = self._extract_title_from_content(html_content)

                    # Set the content
                    print(f"Setting new content in web view: {content_path}")
                    self.web_view.page().setContent(html_content.encode(), "text/html", file_url)
                    self.last_content_path = content_path
                    self.content_loaded = True
                    return title

                except Exception as e:
                    print(f"Error loading HTML content: {str(e)}")
                    self.web_view.setHtml(f"<div>Error loading content: {str(e)}</div>")
                    return "Error"

            elif content_path.endswith('.png'):
                try:
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>{self.current_url}</title>
                        <style>
                            body {{ 
                                margin: 0; 
                                padding: 0; 
                                background-color: { "#212121" if self.servo_thread.dark_mode else "#fff" };
                            }}
                            .info-bar {{ 
                                background-color: { "#2d2d2d" if self.servo_thread.dark_mode else "#E8F5E9" };
                                padding: 0.5%; 
                                font-size: 0.9em; 
                                color: { "#e0e0e0" if self.servo_thread.dark_mode else "#333" }; 
                            }}
                            img {{ width: 100%; height: auto; border-radius: 8px; }}
                        </style>
                    </head>
                    <body>
                        <img src="file:///{content_path.replace('\\', '/')}" />
                        <div class="info-bar">
                            <p>Viewing: {self.current_url}</p>
                        </div>
                    </body>
                    </html>
                    """
                    print(f"Setting PNG content in web view: {content_path}")
                    self.web_view.setHtml(html_content, baseUrl=QUrl(self.current_url))
                    self.last_content_path = content_path
                except Exception as e:
                    print(f"Error displaying PNG: {str(e)}")
                    self.web_view.load(QUrl.fromLocalFile(content_path))
                parsed_url = urllib.parse.urlparse(self.current_url)
                domain = parsed_url.netloc or "Unknown"
                return domain
            else:
                try:
                    file_url = QUrl.fromLocalFile(content_path)
                    print(f"Loading unsupported file type: {content_path}")
                    self.web_view.load(file_url)
                    self.last_content_path = content_path
                except:
                    self.web_view.setHtml(f"<div>Unsupported content: {content_path}</div>")
                return "Error"
        finally:
            self.update_lock.unlock()
            print(f"Content update completed for: {content_path}")

    def _extract_title_from_content(self, html_content):
        title_start = html_content.find("<title>")
        title_end = html_content.find("</title>")
        if title_start != -1 and title_end != -1:
            return html_content[title_start + 7:title_end]
        if self.current_url:
            parsed_url = urllib.parse.urlparse(self.current_url)
            return parsed_url.netloc or "New Tab"
        return "New Tab"

    def _extract_title_from_path(self, content_path):
        if content_path.endswith(('.html', '.htm')):
            try:
                with open(content_path, 'r', encoding='utf-8', errors='replace') as f:
                    return self._extract_title_from_content(f.read())
            except:
                return None
        return None

class CustomWebRenderer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Servo Web Browser")
        
        # Initialize main application window
        screen = QApplication.primaryScreen()
        screen_size = screen.availableGeometry()
        width = int(screen_size.width() * 1.00)
        height = int(screen_size.height() * 1.00)
        self.resize(width, height)
        self.move(int((screen_size.width() - width) / 2), int((screen_size.height() - height) / 2))
        self.setMinimumSize(int(screen_size.width() * 0.5), int(screen_size.height() * 0.5))

        self.tab_counter = 0
        self.tabs_dict = {}
        self.current_search_engine = "https://duckduckgo.com/?t=h_&q={query}&ia=web"
        
        self.history_processor = BrowserHistoryProcessor("./browser_data/history.json")
        
        self.servo_thread = ServoThread(self)
        self.servo_thread.content_ready.connect(self.update_tab_content)
        self.servo_thread.loading_started.connect(self.show_loading)
        self.servo_thread.loading_finished.connect(self.hide_loading)

        self.new_tab_button = QToolButton()
        self.dark_mode_manager = DarkModeManager(self, self.servo_thread, self.tabs_dict, None, self.new_tab_button)
        self.servo_thread.dark_mode_manager = self.dark_mode_manager

        self.browser_layout = BrowserLayout(self, self.dark_mode_manager, self.servo_thread, self.tabs_dict, self.new_tab_button)
        self.setCentralWidget(self.browser_layout)

        self.dark_mode_manager.tabs = self.browser_layout.get_tabs()
        
        self.servo_thread.start()

        # Initialize shortcuts and default background image
        self.shortcuts_file = "./browser_data/shortcuts.json"
        self.shortcuts = []
        self.background_image = None
        self.load_shortcuts()
        
        self.add_starting_screen()
        
        self.force_fallback = True
        self.servo_thread.set_force_fallback(self.force_fallback)

        self.create_menu()
    
    def load_shortcuts(self):
        default_shortcuts = [
            {"title": "Acko", "url": "https://www.acko.com", "icon": "A"},
            {"title": "Play Games", "url": "https://www.playgames.com", "icon": "🎮"},
            {"title": "Policybazaar", "url": "https://www.policybazaar.com", "icon": "P"},
            {"title": "Home Loans", "url": "https://www.homeloans.com", "icon": "🏠"},
            {"title": "Booking.com", "url": "https://www.booking.com", "icon": "B"},
            {"title": "Airbnb", "url": "https://www.airbnb.com", "icon": "A"},
            {"title": "Agoda", "url": "https://www.agoda.com", "icon": "A"},
            {"title": "World of Warships", "url": "https://www.worldofwarships.com", "icon": "W"},
            {"title": "Trip.com", "url": "https://www.trip.com", "icon": "T"},
            {"title": "Hotels Combined", "url": "https://www.hotelscombined.com", "icon": "H"}
        ]
        
        # Set the default background image path to the new image
        local_image_path = os.path.join(os.getcwd(), "images", "img.jpg")
        fallback_url = "https://via.placeholder.com/800x400"
        
        print(f"Current working directory: {os.getcwd()}")
        print(f"Looking for image at: {local_image_path}")
        print(f"Does file exist? {os.path.exists(local_image_path)}")
        
        if os.path.exists(local_image_path):
            print("Background image found")
            try:
                file_url = QUrl.fromLocalFile(local_image_path).toString()
                print(f"Converted to file URL: {file_url}")
                self.background_image = file_url
            except Exception as e:
                print(f"Error converting to file URL: {e}")
                self.background_image = fallback_url
        else:
            print(f"Background image not found at {local_image_path}, using fallback")
            self.background_image = fallback_url
        
        try:
            if not os.path.exists(self.shortcuts_file):
                print("Creating new shortcuts file")
                os.makedirs(os.path.dirname(self.shortcuts_file), exist_ok=True)
                with open(self.shortcuts_file, 'w') as f:
                    json.dump({
                        "shortcuts": default_shortcuts,
                        "background_image": self.background_image
                    }, f, indent=2)
                self.shortcuts = default_shortcuts
            else:
                print("Loading existing shortcuts file")
                with open(self.shortcuts_file, 'r') as f:
                    data = json.load(f)
                    self.shortcuts = data.get("shortcuts", default_shortcuts)
                    # Always use the current background image setting
                    data["background_image"] = self.background_image
                    with open(self.shortcuts_file, 'w') as f:
                        json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error loading shortcuts: {e}")
            self.shortcuts = default_shortcuts

    def save_shortcuts(self):
        try:
            with open(self.shortcuts_file, 'w') as f:
                json.dump({
                    "shortcuts": self.shortcuts,
                    "background_image": self.background_image
                }, f, indent=2)
            print("Shortcuts and background image saved successfully")
        except Exception as e:
            print(f"Error saving shortcuts: {e}")

    def add_shortcut(self, tab):
        print("add_shortcut called")
        url, ok = QInputDialog.getText(self, "Add Shortcut", "Enter URL (e.g., https://example.com):")
        if ok and url.strip():
            if not url.startswith(('http://', 'https://')):
                url = "https://" + url
            title, ok = QInputDialog.getText(self, "Add Shortcut", "Enter title for the shortcut:")
            if ok and title.strip():
                icon, ok = QInputDialog.getText(self, "Add Shortcut", "Enter icon (e.g., letter or emoji):", text="S")
                if ok and icon.strip():
                    self.shortcuts.append({"title": title, "url": url, "icon": icon})
                    self.save_shortcuts()
                    print(f"New shortcut added: {title}, {url}, {icon}")
                    if tab.current_url == "about:start":
                        print("Updating start page with new shortcut")
                        self.update_starting_screen(tab)
                        tab.url_bar.setText("about:start")
                    else:
                        print("Current tab is not about:start, no update performed")
                else:
                    print("Icon input cancelled or empty")
            else:
                print("URL input cancelled or empty")

    def add_image(self, tab):
        print("add_image called")
        try:
            # Open file dialog with simple configuration
            image_path, _ = QFileDialog.getOpenFileName(
                parent=self,
                caption="Select Background Image",
                directory=os.path.expanduser("~"),
                filter="Image Files (*.jpg *.jpeg *.png *.gif *.bmp);;All Files (*)"
            )
            
            if not image_path:
                print("No image selected")
                return
                
            print(f"Selected file path: {image_path}")
            
            # Verify the file exists
            if not os.path.exists(image_path):
                raise Exception("Selected file does not exist")
            
            # Create images directory if it doesn't exist
            images_dir = os.path.join(os.getcwd(), "images")
            os.makedirs(images_dir, exist_ok=True)
            
            # Copy the selected image to the images directory
            import shutil
            new_image_path = os.path.join(images_dir, "img.jpg")
            shutil.copy2(image_path, new_image_path)
            print(f"Copied image to: {new_image_path}")
            
            # Convert to file URL
            file_url = QUrl.fromLocalFile(new_image_path).toString()
            print(f"Converted to file URL: {file_url}")
            
            # Update the background image
            self.background_image = file_url
            
            # Save the changes
            self.save_shortcuts()
            print(f"Updated background image to: {self.background_image}")
            
            # Force refresh all tabs showing the start page
            for tab_id, tab in self.tabs_dict.items():
                if hasattr(tab, 'current_url') and tab.current_url == "about:start":
                    print(f"Refreshing start page for tab: {tab_id}")
                    # Generate new HTML content
                    temp_html = self.generate_starting_screen_html()
                    if temp_html:
                        # Force a complete reload
                        tab.web_view.setHtml("")  # Clear current content
                        tab.update_content(temp_html)
                        tab.url_bar.setText("about:start")
            
            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"Background image updated successfully!\nFile: {os.path.basename(image_path)}",
                QMessageBox.Ok
            )
        
        except Exception as e:
            print(f"Error setting background image: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to set background image:\n{str(e)}",
                QMessageBox.Ok
            )

    def generate_starting_screen_html(self):
        dark_mode = self.dark_mode_manager.is_dark_mode()
        dark_mode_css = self.dark_mode_manager.get_content_css()
        
        # Generate shortcut buttons with static positioning
        shortcut_buttons = ""
        for i, shortcut in enumerate(self.shortcuts):
            shortcut_buttons += f"""
                <a class="shortcut-button" href="{shortcut['url']}" onclick="window.location.href='{shortcut['url']}'; return false;">
                    <div class="icon">{shortcut['icon']}</div>
                    <div class="label">{shortcut['title']}</div>
                </a>
            """
        
        # Use the current background image
        background_image_url = self.background_image or "file:///C:/Users/cc/Desktop/Browser%20Engine/images/img.jpg"
        print(f"Using background image URL: {background_image_url}")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Start Page</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    overflow: hidden;
                    height: 100vh;
                    width: 100vw;
                    position: relative;
                    background: url('{background_image_url}') no-repeat center center fixed;
                    background-size: cover;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .overlay {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.4);
                    z-index: 1;
                }}
                .container {{
                    position: relative;
                    z-index: 2;
                    width: 100%;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    box-sizing: border-box;
                }}
                .search-container {{
                    width: 100%;
                    max-width: 800px;
                    margin: 0 auto 60px auto;
                }}
                .search-bar {{
                    width: 100%;
                    background: {'rgba(45, 45, 45, 0.9)' if dark_mode else 'rgba(255, 255, 255, 0.9)'};
                    border-radius: 30px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    padding: 5px 20px;
                    position: relative;
                    border: 2px solid {'#424242' if dark_mode else '#e0e0e0'};
                }}
                .search-bar input {{
                    width: 100%;
                    height: 60px;
                    border: none;
                    background: transparent;
                    padding: 0 25px;
                    font-size: 22px;
                    color: {'#e0e0e0' if dark_mode else '#333'};
                    outline: none;
                }}
                .search-bar input::placeholder {{
                    color: {'#999' if dark_mode else '#666'};
                    font-size: 22px;
                    opacity: 0.8;
                }}
                .shortcuts-grid {{
                    display: grid;
                    grid-template-columns: repeat(4, 220px);
                    gap: 30px;
                    justify-content: center;
                    margin: 0 auto;
                    width: fit-content;
                }}
                .shortcut-button {{
                    background-color: {'#2d2d2d' if dark_mode else '#ffffff'};
                    border: 1px solid {'#424242' if dark_mode else '#e0e0e0'};
                    border-radius: 16px;
                    width: 220px;
                    height: 180px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    text-decoration: none;
                }}
                .shortcut-button .icon {{
                    font-size: 52px;
                    margin-bottom: 16px;
                    color: {'#e0e0e0' if dark_mode else '#333'};
                    pointer-events: none;
                }}
                .shortcut-button .label {{
                    font-size: 20px;
                    color: {'#e0e0e0' if dark_mode else '#333'};
                    text-align: center;
                    max-width: 90%;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    pointer-events: none;
                }}
                .add-shortcut {{
                    font-size: 42px;
                    color: {'#ff9500' if dark_mode else '#007bff'};
                }}
            </style>
        </head>
        <body>
            <div class="overlay"></div>
            <div class="container">
                <div class="search-container">
                    <div class="search-bar">
                        <input type="text" placeholder="Search with DuckDuckGo" 
                               onkeypress="if(event.key === 'Enter') window.location.href='https://duckduckgo.com/?q=' + encodeURIComponent(this.value);">
                    </div>
                </div>
                <div class="shortcuts-grid">
                    {shortcut_buttons}
                    <a class="shortcut-button add-shortcut" href="about:add-shortcut">
                        <div class="icon">+</div>
                        <div class="label">Add Shortcut</div>
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        temp_html = os.path.join(self.servo_thread.temp_dir, f"start_page_{self.tab_counter}.html")
        try:
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Written HTML to: {temp_html}")
        except Exception as e:
            print(f"Failed to write HTML: {str(e)}")
            return None
        return temp_html

    def add_starting_screen(self, replace=False):
        temp_html = self.generate_starting_screen_html()
        if not temp_html:
            print("Failed to generate start page HTML")
            return
        
        self.tab_counter += 1
        tab_id = f"tab_{self.tab_counter}"
        new_tab = BrowserTab(self.servo_thread, tab_id, "about:start", self.dark_mode_manager, self.history_processor, self)
        new_tab.default_search_engine = self.current_search_engine
        new_tab.current_url = "about:start"
        
        # Set initial content without triggering reload
        new_tab.last_content_path = temp_html
        new_tab.update_content(temp_html)
        
        if replace:
            current_index = self.browser_layout.get_tabs().currentIndex()
            if current_index >= 0:
                self.browser_layout.get_tabs().removeTab(current_index)
                self.tabs_dict.pop(list(self.tabs_dict.keys())[current_index], None)
                
        self.browser_layout.add_tab(new_tab, "Start Page")
        self.tabs_dict[tab_id] = new_tab
        print(f"Added/updated starting screen tab with ID: {tab_id}")

    def update_starting_screen(self, tab):
        # Only update if the tab is currently showing the start page
        if tab.current_url == "about:start":
            temp_html = self.generate_starting_screen_html()
            if temp_html and temp_html != tab.last_content_path:
                tab.update_content(temp_html)
                print(f"Updated start page content for tab: {tab.tab_id}")
        else:
            print("Tab is not showing start page, skipping update")

    def create_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.triggered.connect(lambda: self.add_new_tab(""))
        file_menu.addAction(new_tab_action)
        reload_action = QAction("Reload Page", self)
        reload_action.setShortcut("F5")
        reload_action.triggered.connect(self.reload_current_page)
        file_menu.addAction(reload_action)
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        search_menu = menu_bar.addMenu("Search Engines")
        duckduckgo_action = QAction("DuckDuckGo", self)
        duckduckgo_action.triggered.connect(lambda: self.set_search_engine("https://duckduckgo.com/?t=h_&q={query}&ia=web"))
        search_menu.addAction(duckduckgo_action)
        google_action = QAction("Google", self)
        google_action.triggered.connect(lambda: self.set_search_engine("https://www.google.com/search?q={query}"))
        search_menu.addAction(google_action)
        bing_action = QAction("Bing", self)
        bing_action.triggered.connect(lambda: self.set_search_engine("https://www.bing.com/search?q={query}"))
        search_menu.addAction(bing_action)
        
        render_menu = menu_bar.addMenu("Rendering")
        force_fallback_action = QAction("Force Fallback Rendering", self)
        force_fallback_action.setCheckable(True)
        force_fallback_action.setChecked(self.force_fallback)
        force_fallback_action.triggered.connect(self.toggle_force_fallback)
        render_menu.addAction(force_fallback_action)
        
        ua_menu = menu_bar.addMenu("User Agent")
        chrome_action = QAction("Chrome", self)
        chrome_action.triggered.connect(lambda: self.set_user_agent(0))
        ua_menu.addAction(chrome_action)
        safari_action = QAction("Safari", self)
        safari_action.triggered.connect(lambda: self.set_user_agent(1))
        ua_menu.addAction(safari_action)
        edge_action = QAction("Edge", self)
        edge_action.triggered.connect(lambda: self.set_user_agent(2))
        ua_menu.addAction(edge_action)
        firefox_action = QAction("Firefox", self)
        firefox_action.triggered.connect(lambda: self.set_user_agent(3))
        ua_menu.addAction(firefox_action)
        
        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def toggle_force_fallback(self, checked):
        self.force_fallback = checked
        self.servo_thread.set_force_fallback(checked)
        self.reload_current_page()
    
    def show_about(self):
        about_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>About</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 2%; 
                    font-size: 1.2em; 
                    background-color: { "#212121" if self.dark_mode_manager.is_dark_mode() else "#fff" }; 
                    color: { "#e0e0e0" if self.dark_mode_manager.is_dark_mode() else "#333" }; 
                }}
            </style>
        </head>
        <body>
            <h2>Servo Web Browser</h2>
            <p>A browser using Servo rendering engine with enhanced fallback</p>
            <p>Version 1.2</p>
            <p>Features improved bot avoidance, ad blocking, and search engine selection</p>
        </body>
        </html>
        """
        current_tab = self.browser_layout.get_tabs().currentWidget()
        if current_tab:
            current_tab.web_view.setHtml(about_html)
            self.browser_layout.get_tabs().setTabText(self.browser_layout.get_tabs().currentIndex(), "About")
    
    def reload_current_page(self):
        current_tab = self.browser_layout.get_tabs().currentWidget()
        if current_tab and hasattr(current_tab, 'url_bar'):
            url = current_tab.url_bar.text()
            if url:
                current_tab.handle_input()
    
    def set_search_engine(self, engine_url):
        self.current_search_engine = engine_url
        for tab_id, tab in self.tabs_dict.items():
            tab.default_search_engine = engine_url
        
        engine_name = "DuckDuckGo" if "duckduckgo" in engine_url else "Google" if "google" in engine_url else "Bing"
        current_tab = self.browser_layout.get_tabs().currentWidget()
        if current_tab:
            notification_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Search Engine Changed</title>
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
                </style>
                <script>
                    setTimeout(function() {{
                        window.history.back();
                    }}, 2000);
                </script>
            </head>
            <body>
                <div class="notification">
                    <h2>Search Engine Changed</h2>
                    <p>Default search engine set to <strong>{engine_name}</strong></p>
                </div>
            </body>
            </html>
            """
            current_tab.web_view.setHtml(notification_html)
            self.browser_layout.get_tabs().setTabText(self.browser_layout.get_tabs().currentIndex(), "Notification")
    
    def set_user_agent(self, ua_index):
        self.servo_thread.set_user_agent(ua_index)
    
    def add_new_tab(self, url):
        self.tab_counter += 1
        tab_id = f"tab_{self.tab_counter}"
        new_tab = BrowserTab(self.servo_thread, tab_id, url, self.dark_mode_manager, self.history_processor, self)
        new_tab.default_search_engine = self.current_search_engine
        tab_title = "New Tab"
        self.browser_layout.add_tab(new_tab, tab_title)
        self.tabs_dict[tab_id] = new_tab
    
    def update_tab_content(self, content_path, tab_id):
        print(f"Updating tab content for tab_id: {tab_id} with content: {content_path}")
        if tab_id in self.tabs_dict:
            tab = self.tabs_dict[tab_id]
            
            # Skip update if content hasn't changed
            if tab.last_content_path == content_path:
                print(f"Skipping update - content unchanged for tab {tab_id}")
                return
            
            # For start page, only update if necessary
            if tab.current_url == "about:start":
                if tab.last_content_path and os.path.exists(tab.last_content_path):
                    print("Skipping start page update - content already loaded")
                    return
            
            title = tab.update_content(content_path)
            idx = self.browser_layout.get_tabs().indexOf(tab)
            if idx != -1:
                tab_title = title[:15] + "..." if len(title) > 15 else title
                self.browser_layout.get_tabs().setTabText(idx, tab_title)

    def show_loading(self, tab_id):
        self.browser_layout.show_loading(tab_id)

    def hide_loading(self, tab_id):
        self.browser_layout.hide_loading(tab_id)

    def close_tab(self, index):
        if self.browser_layout.get_tabs().count() > 1:
            tab = self.browser_layout.get_tabs().widget(index)
            for tab_id, tab_obj in list(self.tabs_dict.items()):
                if tab_obj == tab:
                    del self.tabs_dict[tab_id]
                    break
            self.browser_layout.get_tabs().removeTab(index)
        else:
            self.close()

    def closeEvent(self, event):
        print("Closing application, stopping ServoThread")
        self.servo_thread.stop()
        if self.servo_thread.isRunning():
            self.servo_thread.terminate()
            self.servo_thread.wait(5000)
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = None
    try:
        window = CustomWebRenderer()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Application failed to start: {str(e)}")
        if window and hasattr(window, 'servo_thread'):
            window.servo_thread.stop()
            if window.servo_thread.isRunning():
                window.servo_thread.terminate()
                window.servo_thread.wait(5000)
        sys.exit(1)