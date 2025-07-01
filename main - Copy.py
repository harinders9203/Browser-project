from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLineEdit, QPushButton, QDialog, 
                            QListWidget, QListWidgetItem, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QUrl, QMutex
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
import os
import json
from datetime import datetime

# Create bookmark icons if they don't exist
if not os.path.exists('bookmark.png'):
    # Create a simple bookmark icon
    from PIL import Image, ImageDraw
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon([(8, 8), (24, 8), (24, 28), (16, 24), (8, 28)], fill=(128, 128, 128, 255))
    img.save('bookmark.png')

if not os.path.exists('bookmark_filled.png'):
    # Create a filled bookmark icon
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon([(8, 8), (24, 8), (24, 28), (16, 24), (8, 28)], fill=(255, 215, 0, 255))
    img.save('bookmark_filled.png')

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget, QAction, QToolButton, QLineEdit, QProgressBar, QHBoxLayout, QPushButton, QInputDialog, QMessageBox, QFileDialog, QSizePolicy, QMenu, QDialog, QListWidget, QListWidgetItem, QToolBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QMutex
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtGui import QIcon
import sys
import subprocess
import requests
import os
import time
import socket
import json
import urllib.parse
import random
import tempfile
import base64
from dark_mode import DarkModeManager
from layout import BrowserLayout
from history import BrowserHistoryProcessor
from vpn_handler import VPNHandler
from adblocker import AdBlocker  # Fix import name
from phishing_detector import PhishingDetector
from bookmarks import BookmarkManager
from bookmark_history_manager import BookmarkHistoryManager
from datetime import datetime

class ServoThread(QThread):
    content_ready = pyqtSignal(str, str)
    loading_started = pyqtSignal(str)
    loading_finished = pyqtSignal(str)
    phishing_detected = pyqtSignal(str, dict)  # Add this signal

    def __init__(self, parent=None, dark_mode_manager=None):
        super().__init__(parent)
        self.running = True
        self.queue = []
        self.port = self._find_free_port()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"
        ]
        self.current_user_agent = random.choice(self.user_agents)
        self.temp_dir = tempfile.mkdtemp(prefix="servo_")
        self.render_timeout = 30
        self.force_fallback = True
        self.dark_mode = False
        self.vpn_enabled = False
        self.dark_mode_manager = dark_mode_manager
        self.ad_blocker = AdBlocker()
        self.ad_blocker_enabled = True
        self.phishing_detector = PhishingDetector()  # Initialize phishing detector

        # Initialize ad blocker with aggressive settings
        print("Initializing ad blocker with aggressive settings...")
        try:
            self.ad_blocker.load_filters()
            print("Ad blocker filters loaded successfully")
        except Exception as e:
            print(f"Error loading ad blocker filters: {e}")
            
        # Force ad blocking to be always on
        self.ad_blocker_enabled = True
        print("Ad blocking enabled with aggressive settings")
        
    def _find_free_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()
        return port
        
    def add_url_to_queue(self, url, tab_id):
        print(f"Adding URL to queue: {url} (tab_id: {tab_id})")
        problematic_sites = ["google", "duckduckgo", "bing", "facebook", "twitter", "instagram", "youtube"]
        if self.force_fallback or any(site in url.lower() for site in problematic_sites):
            print("Using fallback rendering due to force_fallback or problematic site")
            self._fallback_rendering(url, tab_id)
        else:
            self.queue.append((url, tab_id))
        
    def run(self):
        print("ServoThread started")
        startupinfo = None
        creationflags = 0
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = subprocess.CREATE_NO_WINDOW

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('localhost', self.port))
        server.listen(5)
        server.settimeout(0.5)
        
        while self.running:
            if self.queue:
                url, tab_id = self.queue.pop(0)
                print(f"Processing URL from queue: {url} (tab_id: {tab_id})")
                print(f"Emitting loading_started signal for tab_id: {tab_id}")
                self.loading_started.emit(tab_id)
                if any(site in url.lower() for site in ["google", "duckduckgo", "bing", "facebook"]):
                    self.render_timeout = 60
                else:
                    self.render_timeout = 30
                output_file = os.path.join(self.temp_dir, f"{tab_id}_{int(time.time())}.png")
                servo_path = r"C:\\Users\\cc\\Desktop\\servo\\target\\release\\servo.exe"
                if not os.path.exists(servo_path):
                    print(f"Error: Servo executable not found at {servo_path}")
                    self._fallback_rendering(url, tab_id)
                    continue
                servo_cmd = [
                    servo_path, url, f"--user-agent={self.current_user_agent}", "--headless",
                    f"--output={output_file}", "--gpu=disabled", "--no-webrender-stats",
                    "--certificate-path=mozilla", "--devtools", f"--ipc-port={self.port}",
                    "--allow-third-party-cookies", "--no-sandbox", "--js-backtrace"
                ]
                if "google" in url.lower() or "duckduckgo" in url.lower() or "bing" in url.lower():
                    servo_cmd.extend(["--disable-http-cache=false", "--max-wait-for-load=30000"])
                try:
                    servo_process = subprocess.Popen(servo_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                    startupinfo=startupinfo, creationflags=creationflags)
                    try:
                        stdout, stderr = servo_process.communicate(timeout=self.render_timeout)
                        if os.path.exists(output_file) and os.path.getsize(output_file) > 5000:
                            print(f"Servo rendering successful, emitting content: {output_file}")
                            self.content_ready.emit(output_file, tab_id)
                        else:
                            print(f"Output file not created or too small for {url}, falling back")
                            self._fallback_rendering(url, tab_id)
                    except subprocess.TimeoutExpired:
                        servo_process.kill()
                        print(f"Timeout rendering {url}, falling back")
                        self._fallback_rendering(url, tab_id)
                    except Exception as e:
                        print(f"Error rendering {url}: {str(e)}")
                        self._fallback_rendering(url, tab_id)
                finally:
                    print(f"Emitting loading_finished signal for tab_id: {tab_id}")
                    self.loading_finished.emit(tab_id)

            try:
                client, addr = server.accept()
                data = client.recv(4096)
                if data:
                    try:
                        message = json.loads(data.decode('utf-8'))
                        if 'event' in message:
                            if message['event'] == 'page_loaded':
                                print("Servo event: page_loaded")
                            elif message['event'] == 'error':
                                print("Servo event: error")
                    except json.JSONDecodeError:
                        pass
                client.close()
            except socket.timeout:
                pass

            time.sleep(0.1)

        server.close()
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except:
            pass
        print("ServoThread stopped")

    def _is_ad_url(self, url):
        """Check if a URL is an ad URL"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            return self.ad_blocker.is_ad_domain(url)
        except:
            return False

    def _fallback_rendering(self, url, tab_id):
        print(f"Starting fallback rendering for {url} (tab_id: {tab_id})")
        print(f"Emitting loading_started signal for tab_id: {tab_id}")
        self.loading_started.emit(tab_id)
        try:
            self.current_user_agent = random.choice(self.user_agents)
            if "google.com" in url.lower():
                self.current_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"

            headers = {
                'User-Agent': self.current_user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'DNT': '1',
                'Sec-Ch-Ua': '"Chromium";v="129", "Not=A?Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
            }

            session = requests.Session()
            
            if "google.com" in url.lower():
                headers['Referer'] = 'https://www.google.com/'
                headers['Origin'] = 'https://www.google.com'
                if url.startswith('http://'):
                    url = 'https://' + url[7:]
                if "www." not in url and "google.com" in url:
                    url = url.replace("google.com", "www.google.com")
                print("Fetching Google page with fallback")
                response = session.get(url, headers=headers, timeout=10)
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Google</title>
                    <style>
                        body {{ 
                            font-family: Arial, sans-serif; 
                            text-align: center; 
                            padding: 2%; 
                            font-size: 1.2em; 
                            background-color: { '#212121' if self.dark_mode else '#f8f9fa' }; 
                            color: { '#e0e0e0' if self.dark_mode else '#333' }; 
                        }}
                        .google-notice {{ 
                            background-color: { '#2d2d2d' if self.dark_mode else '#f8f9fa' }; 
                            padding: 2%; 
                            border-radius: 8px; 
                            margin: 2% auto; 
                            max-width: 50%; 
                        }}
                        .search-box {{ margin: 2% auto; width: 80%; max-width: 50%; }}
                        input[type="text"] {{ 
                            width: 70%; 
                            padding: 1%; 
                            font-size: 1.2em; 
                            border: 1px solid { '#424242' if self.dark_mode else '#dfe1e5' }; 
                            border-radius: 24px; 
                            background-color: { '#2d2d2d' if self.dark_mode else '#fff' }; 
                            color: { '#e0e0e0' if self.dark_mode else '#333' }; 
                        }}
                        button {{ 
                            padding: 1% 2%; 
                            margin-left: 1%; 
                            background-color: { '#2d2d2d' if self.dark_mode else '#f8f9fa' }; 
                            border: 1px solid { '#424242' if self.dark_mode else '#f8f9fa' }; 
                            border-radius: 4px; 
                            cursor: pointer; 
                            font-size: 1em; 
                            color: { '#e0e0e0' if self.dark_mode else '#333' }; 
                        }}
                        button:hover {{ background-color: { '#3f3f3f' if self.dark_mode else '#e0e0e0' }; }}
                    </style>
                </head>
                <body>
                    <div class="google-notice">
                        <h2>Google Search</h2>
                        <p>Google's homepage isn't displaying correctly due to encoding issues.</p>
                        <p>You can still search using the form below:</p>
                    </div>
                    <div class="search-box">
                        <form action="https://www.google.com/search" method="GET">
                            <input type="text" name="q" placeholder="Search Google...">
                            <button type="submit">Search</button>
                        </form>
                    </div>
                </body>
                </html>
                """
                temp_html = os.path.join(self.temp_dir, f"{tab_id}_google_fallback.html")
                with open(temp_html, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"Emitting Google fallback content: {temp_html}")
                self.content_ready.emit(temp_html, tab_id)
                self.loading_finished.emit(tab_id)
                return
            elif "duckduckgo.com" in url.lower():
                print("Fetching DuckDuckGo page with fallback")
                parsed_url = urllib.parse.urlparse(url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if 'q' in query_params:
                    search_query = query_params['q'][0]
                    duckduckgo_url = "https://duckduckgo.com/"
                    post_data = {'q': search_query, 't': 'h_', 'ia': 'web'}
                    special_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Origin': 'https://duckduckgo.com',
                        'Referer': 'https://duckduckgo.com/',
                    }
                    response = session.post(duckduckgo_url, data=post_data, headers=special_headers, timeout=15)
                else:
                    response = session.get(url, headers=headers, timeout=15)
                
                print(f"Response status code: {response.status_code}")
                if response.status_code == 200:
                    try:
                        html_content = response.content.decode('utf-8', errors='replace')
                        # Apply ad blocking
                        if self.ad_blocker_enabled:
                            html_content = self._block_ads(html_content, url)
                        print(f"Raw HTML length before processing: {len(html_content)}")
                    except Exception as e:
                        print(f"Error decoding content: {str(e)}")
                        html_content = response.text
                        # Apply ad blocking
                        if self.ad_blocker_enabled:
                            html_content = self._block_ads(html_content, url)
                        print(f"Fallback text length: {len(html_content)}")
                else:
                    html_content = f"""
                    <div style="padding: 2%; font-family: Arial; font-size: 1.2em; background-color: { '#212121' if self.dark_mode else '#fff' }; color: { '#e0e0e0' if self.dark_mode else '#333' };">
                        <h2>Error</h2>
                        <p>Failed to load {url} (Status: {response.status_code})</p>
                    </div>
                    """

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
                        # Apply ad blocking
                        if self.ad_blocker_enabled:
                            html_content = self._block_ads(html_content, url)
                    except Exception as e:
                        print(f"Error decoding content: {str(e)}")
                        html_content = response.text
                        # Apply ad blocking
                        if self.ad_blocker_enabled:
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
                        background-color: {"#212121" if self.dark_mode else "#fff"};
                        color: {"#e0e0e0" if self.dark_mode else "#333"};
                    }}
                    .error-container {{
                        background-color: {"#2d2d2d" if self.dark_mode else "#fff3f3"};
                        border-left: 4px solid {"#ff6d6d" if self.dark_mode else "#e74c3c"};
                        padding: 2%;
                        border-radius: 4px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    h2 {{margin-top: 0; color: {"#ff6d6d" if self.dark_mode else "#e74c3c"};}}
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
        """Block ads in HTML content"""
        if not self.ad_blocker_enabled:
            return html_content
            
        try:
            # First check if the domain itself is an ad domain
            if self._is_ad_url(base_url):
                return "<html><body><h1>Ad Blocked</h1><p>This domain has been blocked by the ad blocker.</p></body></html>"
                
            # Block ads in the content
            blocked_content = self.ad_blocker.block_ads(html_content)
            
            # Block security popups
            blocked_content = self.ad_blocker.block_security_popups(blocked_content)
            
            return blocked_content
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
        self.urlChanged.connect(self.on_url_changed)
        self.loadFinished.connect(self.on_load_finished)

    def on_url_changed(self, url):
        """Handle URL changes"""
        if url.isValid():
            url_str = url.toString()
            self.parent_tab.url_bar.setText(url_str)
            self.parent_tab.current_url = url_str
            # Record in history
            if not url_str.startswith('about:'):
                title = self.title()
                if not title:
                    title = url_str
                self.parent_tab.add_to_history(url_str, title)
            self.parent_tab.update_bookmark_button()

    def on_load_finished(self, success):
        """Handle page load completion"""
        if success:
            url = self.url().toString()
            title = self.title()
            if not title:
                title = url
            # Update history with final title
            if not url.startswith('about:'):
                self.parent_tab.add_to_history(url, title)

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
        self.current_url = url
        self.dark_mode_manager = dark_mode_manager
        self.history_processor = history_processor
        self.parent_renderer = parent_renderer
        
        # Initialize state variables
        self.bookmarks = []
        self.history = []
        self.vpn_handler = None
        self.content_loaded = False
        self.last_content_path = None
        self.update_lock = QMutex()
        self.handling_input = False
        self.default_search_engine = "https://duckduckgo.com/?t=h_&q={query}&ia=web"
        self.bookmark_manager = None  # Will be set by CustomWebRenderer
        self.is_loading = False  # Track loading state

        # Load data
        self.load_bookmarks()
        self.load_history()

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create navigation bar
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(5, 5, 5, 5)
        nav_layout.setSpacing(5)

        # Define common button style and size
        button_size = 36  # Slightly larger buttons for better visibility
        button_style = """
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
                font-size: 16px;
                min-width: %dpx;
                max-width: %dpx;
                min-height: %dpx;
                max-height: %dpx;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #ced4da;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """ % (button_size, button_size, button_size, button_size)

        # Back button
        self.back_button = QPushButton("⬅️")
        self.back_button.setToolTip("Go back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setStyleSheet(button_style)
        nav_layout.addWidget(self.back_button)

        # Forward button
        self.forward_button = QPushButton("➡️")
        self.forward_button.setToolTip("Go forward")
        self.forward_button.clicked.connect(self.go_forward)
        self.forward_button.setStyleSheet(button_style)
        nav_layout.addWidget(self.forward_button)

        # Reload button
        self.reload_button = QPushButton("🔄")
        self.reload_button.setToolTip("Reload page")
        self.reload_button.clicked.connect(self.reload_page)
        self.reload_button.setStyleSheet(button_style)
        nav_layout.addWidget(self.reload_button)

        # URL bar with matching height
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search term")
        self.url_bar.returnPressed.connect(self.handle_input)
        self.url_bar.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 14px;
                min-height: %dpx;
                max-height: %dpx;
            }
            QLineEdit:focus {
                border-color: #86b7fe;
                outline: 0;
                box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
            }
        """ % (button_size, button_size))
        nav_layout.addWidget(self.url_bar)

        # Show Bookmarks button
        self.show_bookmarks_button = QPushButton("📑")
        self.show_bookmarks_button.setToolTip("Show bookmarks")
        self.show_bookmarks_button.clicked.connect(self.show_bookmarks)
        self.show_bookmarks_button.setStyleSheet(button_style)
        nav_layout.addWidget(self.show_bookmarks_button)

        # Toggle Bookmark button
        self.bookmark_button = QPushButton("☆")
        self.bookmark_button.setToolTip("Add bookmark")
        self.bookmark_button.clicked.connect(self.toggle_bookmark)
        self.bookmark_button.setStyleSheet(button_style)
        nav_layout.addWidget(self.bookmark_button)

        # History button
        self.history_button = QPushButton("🕒")
        self.history_button.setToolTip("Show history")
        self.history_button.clicked.connect(self.show_history)
        self.history_button.setStyleSheet(button_style)
        nav_layout.addWidget(self.history_button)

        layout.addLayout(nav_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximumHeight(2)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Web view
        self.web_view = QWebEngineView()
        self.web_page = CustomWebEnginePage(self)
        self.web_view.setPage(self.web_page)
        
        # Connect loading signals
        self.web_view.loadStarted.connect(self._on_load_started)
        self.web_view.loadProgress.connect(self._on_load_progress)
        self.web_view.loadFinished.connect(self._on_load_finished)
        
        layout.addWidget(self.web_view)

        self.setLayout(layout)
        self.update_url_bar_style()
        self.update_bookmark_button()

        if url:
            self.navigate_to(url)

        self.servo_thread.phishing_detected.connect(self.show_phishing_warning)  # Connect to phishing signal

    def _on_load_started(self):
        """Handle web view load started"""
        self.is_loading = True
        self.progress.show()
        if self.parent_renderer:
            self.parent_renderer.show_loading(self.tab_id)

    def _on_load_progress(self, progress):
        """Handle web view load progress"""
        self.progress.setValue(progress)

    def _on_load_finished(self, success):
        """Handle web view load finished"""
        self.is_loading = False
        self.progress.hide()
        if self.parent_renderer:
            self.parent_renderer.hide_loading(self.tab_id)

    def load_bookmarks(self):
        """Load bookmarks from file"""
        try:
            if os.path.exists('bookmarks.json'):
                with open('bookmarks.json', 'r') as f:
                    self.bookmarks = json.load(f)
            else:
                self.bookmarks = []
        except Exception as e:
            print(f"Error loading bookmarks: {e}")
            self.bookmarks = []

    def save_bookmarks(self):
        """Save bookmarks to file"""
        try:
            with open('bookmarks.json', 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")

    def load_history(self):
        """Load history from file"""
        try:
            if os.path.exists('history.json'):
                with open('history.json', 'r') as f:
                    self.history = json.load(f)
            else:
                self.history = []
        except Exception as e:
            print(f"Error loading history: {e}")
            self.history = []

    def save_history(self):
        """Save history to file"""
        try:
            with open('history.json', 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_to_history(self, url, title):
        """Add a URL to history"""
        if not url or not title:
            return
            
        # Remove any existing entry with the same URL
        self.history = [entry for entry in self.history if entry['url'] != url]
        
        # Add new entry at the beginning
        self.history.insert(0, {
            'url': url,
            'title': title,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only the last 100 entries
        if len(self.history) > 100:
            self.history = self.history[:100]
            
        self.save_history()

    def toggle_bookmark(self):
        """Toggle bookmark for current page"""
        current_url = self.url_bar.text()
        if not current_url:
            return

        # Check if already bookmarked
        for bookmark in self.bookmarks:
            if bookmark['url'] == current_url:
                # Remove existing bookmark
                self.bookmarks.remove(bookmark)
                self.save_bookmarks()
                self.update_bookmark_button()
                return

        # Add new bookmark
        def html_ready(html):
            title = self._extract_title_from_content(html)
            if not title:
                title = current_url

            self.bookmarks.append({
                'url': current_url,
                'title': title,
                'timestamp': datetime.now().isoformat()
            })
            self.save_bookmarks()
            self.update_bookmark_button()

        # Get HTML asynchronously
        self.web_view.page().toHtml(html_ready)

    def update_bookmark_button(self):
        """Update bookmark button state"""
        current_url = self.url_bar.text()
        is_bookmarked = any(bookmark['url'] == current_url for bookmark in self.bookmarks)
        # Use filled star for bookmarked pages, empty star for non-bookmarked
        self.bookmark_button.setText("⭐" if is_bookmarked else "☆")
        self.bookmark_button.setToolTip("Remove bookmark" if is_bookmarked else "Add bookmark")
        
        # Update the button style to highlight when bookmarked
        if is_bookmarked:
            self.bookmark_button.setStyleSheet("""
                QPushButton {
                    color: #FFD700;  /* Gold color for bookmarked */
                    font-size: 16px;
                }
                QPushButton:hover {
                    color: #FFA500;  /* Darker gold on hover */
                }
            """)
        else:
            self.bookmark_button.setStyleSheet("")  # Reset to default style

    def show_bookmarks(self):
        """Show bookmarks dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Bookmarks")
        dialog.setMinimumSize(400, 500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 10px;
            }
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #e7f5ff;
                color: #007bff;
                border: none;
            }
            QListWidget::item:hover:!selected {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 2px solid #e9ecef;
                border-radius: 20px;
                padding: 8px 20px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #e7f5ff;
                color: #007bff;
                border: 2px solid #007bff;
            }
            QPushButton:pressed {
                background-color: #007bff;
                color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Create search bar
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search bookmarks...")
        layout.addWidget(search_bar)
        
        # Create list widget for bookmarks
        list_widget = QListWidget()
        layout.addWidget(list_widget)
        
        def load_bookmarks():
            list_widget.clear()
            for bookmark in self.bookmarks:
                item = QListWidgetItem(f"{bookmark['title']} - {bookmark['url']}")
                item.setData(Qt.UserRole, bookmark['url'])
                list_widget.addItem(item)
        
        def search_bookmarks():
            query = search_bar.text().lower()
            list_widget.clear()
            for bookmark in self.bookmarks:
                if query in bookmark['title'].lower() or query in bookmark['url'].lower():
                    item = QListWidgetItem(f"{bookmark['title']} - {bookmark['url']}")
                    item.setData(Qt.UserRole, bookmark['url'])
                    list_widget.addItem(item)
        
        def open_bookmark():
            current_item = list_widget.currentItem()
            if current_item:
                url = current_item.data(Qt.UserRole)
                self.navigate_to(url)
                dialog.close()
        
        def delete_bookmark():
            current_item = list_widget.currentItem()
            if current_item:
                url = current_item.data(Qt.UserRole)
                self.bookmarks = [b for b in self.bookmarks if b['url'] != url]
                self.save_bookmarks()
                load_bookmarks()
                self.update_bookmark_button()
        
        def clear_all_bookmarks():
            reply = QMessageBox.question(
                dialog, 
                "Clear Bookmarks",
                "Are you sure you want to clear all bookmarks?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.bookmarks = []
                self.save_bookmarks()
                load_bookmarks()
                self.update_bookmark_button()
        
        # Connect signals
        search_bar.textChanged.connect(search_bookmarks)
        list_widget.itemDoubleClicked.connect(open_bookmark)
        
        # Create buttons
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        
        open_button = QPushButton("Open")
        delete_button = QPushButton("Delete")
        clear_button = QPushButton("Clear All")
        close_button = QPushButton("Close")

        open_button.clicked.connect(open_bookmark)
        delete_button.clicked.connect(delete_bookmark)
        clear_button.clicked.connect(clear_all_bookmarks)
        close_button.clicked.connect(dialog.close)

        buttons.addWidget(open_button)
        buttons.addWidget(delete_button)
        buttons.addWidget(clear_button)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        # Load initial bookmarks
        load_bookmarks()
        dialog.exec_()

    def show_history(self):
        """Show history dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("History")
        dialog.setMinimumSize(500, 600)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 10px;
            }
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #e7f5ff;
                color: #007bff;
                border: none;
            }
            QListWidget::item:hover:!selected {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 2px solid #e9ecef;
                border-radius: 20px;
                padding: 8px 20px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #e7f5ff;
                color: #007bff;
                border: 2px solid #007bff;
            }
            QPushButton:pressed {
                background-color: #007bff;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 14px;
                margin: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Create search bar
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search history...")
        layout.addWidget(search_bar)
        
        # Create list widget for history
        list_widget = QListWidget()
        layout.addWidget(list_widget)
        
        def load_history():
            list_widget.clear()
            for entry in self.history:
                item = QListWidgetItem(f"{entry['title']} - {entry['url']}")
                item.setData(Qt.UserRole, entry['url'])
                list_widget.addItem(item)
        
        def search_history():
            query = search_bar.text().lower()
            list_widget.clear()
            for entry in self.history:
                if query in entry['title'].lower() or query in entry['url'].lower():
                    item = QListWidgetItem(f"{entry['title']} - {entry['url']}")
                    item.setData(Qt.UserRole, entry['url'])
                    list_widget.addItem(item)
        
        def open_history_entry():
            current_item = list_widget.currentItem()
            if current_item:
                url = current_item.data(Qt.UserRole)
                self.navigate_to(url)
                dialog.close()
        
        def delete_history_entry():
            current_item = list_widget.currentItem()
            if current_item:
                url = current_item.data(Qt.UserRole)
                self.history = [entry for entry in self.history if entry['url'] != url]
                self.save_history()
                load_history()
        
        def clear_all_history():
            reply = QMessageBox.question(
                dialog, 
                "Clear History",
                "Are you sure you want to clear all history?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.history = []
                self.save_history()
                load_history()
        
        # Connect signals
        search_bar.textChanged.connect(search_history)
        list_widget.itemDoubleClicked.connect(open_history_entry)
        
        # Create buttons
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        
        open_button = QPushButton("Open")
        delete_button = QPushButton("Delete")
        clear_button = QPushButton("Clear All")
        close_button = QPushButton("Close")

        open_button.clicked.connect(open_history_entry)
        delete_button.clicked.connect(delete_history_entry)
        clear_button.clicked.connect(clear_all_history)
        close_button.clicked.connect(dialog.close)

        buttons.addWidget(open_button)
        buttons.addWidget(delete_button)
        buttons.addWidget(clear_button)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        # Load initial history
        load_history()
        dialog.exec_()

    def open_bookmark(self, list_widget):
        """Open selected bookmark"""
        current_item = list_widget.currentItem()
        if current_item:
            url = current_item.data(Qt.UserRole)
            self.url_bar.setText(url)
            self.handle_input()

    def delete_bookmark(self, list_widget):
        """Delete selected bookmark"""
        current_item = list_widget.currentItem()
        if current_item:
            url = current_item.data(Qt.UserRole)
            self.bookmarks = [b for b in self.bookmarks if b['url'] != url]
            self.save_bookmarks()
            list_widget.takeItem(list_widget.row(current_item))
            self.update_bookmark_button()

    def update_url_bar_style(self, dark_mode=False):
        """Update URL bar style based on dark mode"""
        if dark_mode:
            url_bar_style = """
                QLineEdit {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 2px solid #424242;
                    border-radius: 20px;
                    padding: 8px 15px;
                    font-size: 14px;
                    selection-background-color: #bb86fc;
                    margin: 5px;
                }
                QLineEdit:hover {
                    border: 2px solid #bb86fc;
                }
                QLineEdit:focus {
                    border: 2px solid #bb86fc;
                    background-color: #333333;
                }
            """
            button_style = """
                QPushButton {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 2px solid #424242;
                    border-radius: 15px;
                    padding: 5px 15px;
                    font-size: 16px;
                    min-width: 30px;
                    min-height: 30px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                    border: 2px solid #bb86fc;
                }
                QPushButton:pressed {
                    background-color: #bb86fc;
                    color: #000000;
                }
                QPushButton:disabled {
                    background-color: #1d1d1d;
                    color: #666666;
                    border: 2px solid #333333;
                }
            """
        else:
            url_bar_style = """
                QLineEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 2px solid #e0e0e0;
                    border-radius: 20px;
                    padding: 8px 15px;
                    font-size: 14px;
                    selection-background-color: #007bff;
                    margin: 5px;
                }
                QLineEdit:hover {
                    border: 2px solid #007bff;
                }
                QLineEdit:focus {
                    border: 2px solid #007bff;
                    background-color: #f8f9fa;
                }
            """
            button_style = """
                QPushButton {
                    background-color: #f8f9fa;
                    color: #333333;
                    border: 2px solid #e0e0e0;
                    border-radius: 15px;
                    padding: 5px 15px;
                    font-size: 16px;
                    min-width: 30px;
                    min-height: 30px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border: 2px solid #007bff;
                }
                QPushButton:pressed {
                    background-color: #007bff;
                    color: #ffffff;
                }
                QPushButton:disabled {
                    background-color: #f1f3f5;
                    color: #adb5bd;
                    border: 2px solid #dee2e6;
                }
            """

        self.url_bar.setStyleSheet(url_bar_style)
        self.back_button.setStyleSheet(button_style)
        self.forward_button.setStyleSheet(button_style)
        self.reload_button.setStyleSheet(button_style)
        self.bookmark_button.setStyleSheet(button_style)
        self.history_button.setStyleSheet(button_style)
        
        # Update button icons with modern emojis
        self.back_button.setText("⬅️")
        self.forward_button.setText("➡️")
        self.reload_button.setText("🔄")
        self.bookmark_button.setText("🔖")
        self.history_button.setText("🕒")

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
            elif input_text == "about:toggle-adblocker" and self.parent_renderer:
                print("Processing about:toggle-adblocker")
                self.parent_renderer.toggle_ad_blocker(self)
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

            # Check for phishing before loading the URL
            result = self.servo_thread.phishing_detector.analyze_url(url)
            if result["is_suspicious"]:
                self.servo_thread.phishing_detected.emit(url, result)
                return

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
        """Go back in history"""
        self.web_view.back()

    def go_forward(self):
        """Go forward in history"""
        self.web_view.forward()

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
                                background-color: {"#212121" if self.servo_thread.dark_mode else "#fff"};
                            }}
                            .info-bar {{ 
                                background-color: {"#2d2d2d" if self.servo_thread.dark_mode else "#E8F5E9"};
                                padding: 0.5%; 
                                font-size: 0.9em; 
                                color: {"#e0e0e0" if self.servo_thread.dark_mode else "#333"}; 
                            }}
                            img {{ width: 100%; height: auto; border-radius: 8px; }}
                        </style>
                    </head>
                    <body>
                        <img src="file:///{content_path.replace(chr(92), '/')}" />
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

    def navigate_to(self, url):
        """Navigate to a specific URL"""
        if url:
            self.url_bar.setText(url)
            self.handle_input()

    def show_phishing_warning(self, url, result):
        """Show a warning if a phishing attempt is detected."""
        if result["is_suspicious"]:
            warning_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>⚠️ Phishing Warning</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 2%; 
                        font-size: 1.2em; 
                        background-color: { "#212121" if self.dark_mode_manager.is_dark_mode() else "#fff" }; 
                        color: { "#e0e0e0" if self.dark_mode_manager.is_dark_mode() else "#333" }; 
                    }}
                    .warning-container {{
                        background-color: { "#2d2d2d" if self.dark_mode_manager.is_dark_mode() else "#fff3f3" };
                        border: 4px solid #ff6b6b;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 50px auto;
                        max-width: 600px;
                    }}
                    .warning-icon {{
                        font-size: 48px;
                        margin-bottom: 20px;
                    }}
                    .reasons {{
                        text-align: left;
                        margin: 20px auto;
                        max-width: 500px;
                    }}
                    .reason-item {{
                        margin: 10px 0;
                        padding: 10px;
                        background-color: { "#3d3d3d" if self.dark_mode_manager.is_dark_mode() else "#ffe6e6" };
                        border-radius: 5px;
                    }}
                    .proceed-button {{
                        background-color: #ff6b6b;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        margin: 10px;
                        font-size: 16px;
                    }}
                    .back-button {{
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        margin: 10px;
                        font-size: 16px;
                    }}
                </style>
                <script>
                    function proceedAnyway() {{
                        window.location.href = "{url}";
                    }}
                    function goBack() {{
                        window.history.back();
                    }}
                </script>
            </head>
            <body>
                <div class="warning-container">
                    <div class="warning-icon">⚠️</div>
                    <h2>Potential Phishing Attempt Detected</h2>
                    <p>This website might be trying to steal your information.</p>
                    <p>Risk Score: {result["score"]}/100</p>
                    <div class="reasons">
                        <h3>Reasons:</h3>
                        {"".join(f'<div class="reason-item">• {reason}</div>' for reason in result["reasons"])}
                    </div>
                    <button class="back-button" onclick="goBack()">Go Back (Recommended)</button>
                    <button class="proceed-button" onclick="proceedAnyway()">Proceed Anyway (Unsafe)</button>
                </div>
            </body>
            </html>
            """
            self.web_view.setHtml(warning_html)
            self.browser_layout.get_tabs().setTabText(self.browser_layout.get_tabs().currentIndex(), "⚠️ Warning")

    def reload_page(self):
        """Reload the current page"""
        if self.current_url:
            self.handle_input()

class CustomWebRenderer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Servo Web Browser")
        self.setMinimumSize(1024, 768)
        
        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: none;
                background-color: #ffffff;
                border-radius: 10px;
                margin-top: -1px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                color: #495057;
                border: none;
                padding: 10px 20px;
                margin: 0 2px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-size: 13px;
                min-width: 150px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #007bff;
                border-bottom: 2px solid #007bff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
                color: #212529;
            }
            QTabBar::close-button {
                image: url(close.png);
                subcontrol-position: right;
                margin: 2px;
            }
            QTabBar::close-button:hover {
                background-color: #ff6b6b;
                border-radius: 2px;
            }
            QToolButton#newTabButton {
                background-color: transparent;
                border: none;
                color: #007bff;
                font-size: 20px;
                padding: 5px;
                margin: 2px;
            }
            QToolButton#newTabButton:hover {
                background-color: #e9ecef;
                border-radius: 5px;
            }
            QProgressBar {
                border: none;
                background-color: transparent;
                height: 2px;
            }
            QProgressBar::chunk {
                background-color: #007bff;
            }
            QMenuBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
            QMenuBar::item {
                padding: 8px 15px;
                background-color: transparent;
                color: #495057;
            }
            QMenuBar::item:selected {
                background-color: #e9ecef;
                color: #007bff;
                border-radius: 5px;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #e9ecef;
                color: #007bff;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #f8f9fa;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #adb5bd;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #007bff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar:horizontal {
                border: none;
                background-color: #f8f9fa;
                height: 10px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background-color: #adb5bd;
                border-radius: 5px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #007bff;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """)
        
        # Initialize main application window
        screen = QApplication.primaryScreen()
        screen_size = screen.availableGeometry()
        width = int(screen_size.width() * 0.8)
        height = int(screen_size.height() * 0.8)
        self.resize(width, height)
        self.move(int((screen_size.width() - width) / 2), int((screen_size.height() - height) / 2))
        self.setMinimumSize(800, 600)

        self.tab_counter = 0
        self.tabs_dict = {}
        self.current_search_engine = "https://duckduckgo.com/?t=h_&q={query}&ia=web"
        
        # Initialize ad blocker
        self.ad_blocker = AdBlocker()
        self.ad_blocker_enabled = True
        self.phishing_detection_enabled = True
        
        self.history_processor = BrowserHistoryProcessor("./browser_data/history.json")
        self.bookmark_manager = BookmarkManager()
        
        # Initialize components
        self.servo_thread = ServoThread(self)
        self.servo_thread.content_ready.connect(self.update_tab_content)
        self.servo_thread.loading_started.connect(self.show_loading)
        self.servo_thread.loading_finished.connect(self.hide_loading)
        self.servo_thread.ad_blocker_enabled = True

        # Create new tab button
        self.new_tab_button = QToolButton()
        self.new_tab_button.setText("+")
        self.new_tab_button.setToolTip("New Tab")
        
        # Initialize dark mode manager
        self.dark_mode_manager = DarkModeManager(self, self.servo_thread, self.tabs_dict, None, self.new_tab_button)
        self.servo_thread.dark_mode_manager = self.dark_mode_manager

        # Create browser layout
        self.browser_layout = BrowserLayout(self, self.dark_mode_manager, self.servo_thread, self.tabs_dict, self.new_tab_button)
        self.setCentralWidget(self.browser_layout)

        # Update dark mode manager with tabs reference
        self.dark_mode_manager.tabs = self.browser_layout.get_tabs()
        
        # Start servo thread
        self.servo_thread.start()

        # Load shortcuts and create initial tab
        self.shortcuts_file = "./browser_data/shortcuts.json"
        self.shortcuts = []
        self.background_image = None
        self.load_shortcuts()
        self.add_starting_screen()
        
        self.force_fallback = True
        self.servo_thread.set_force_fallback(self.force_fallback)

        # Create menu bar
        self.create_menu()

    def toggle_dark_mode(self):
        """Toggle dark mode on/off"""
        if hasattr(self, 'dark_mode_manager') and self.dark_mode_manager:
            self.dark_mode_manager.toggle_dark_mode()
            # Update the dark mode button text
            if hasattr(self, 'dark_mode_btn'):
                self.dark_mode_btn.setText(f"Dark Mode: {'On' if self.dark_mode_manager.is_dark_mode() else 'Off'}")
                self.dark_mode_btn.setChecked(self.dark_mode_manager.is_dark_mode())
            
            # Update all tabs with dark mode
            for tab_id, tab in self.tabs_dict.items():
                tab.update_url_bar_style(self.dark_mode_manager.is_dark_mode())
                if tab.current_url == "about:start":
                    self.update_starting_screen(tab)
                tab.apply_dark_mode_to_content(self.dark_mode_manager.is_dark_mode())
            
            # Update the application style
            self.update_application_style()

    def update_application_style(self):
        """Update the application style based on dark mode state"""
        dark_mode = self.dark_mode_manager.is_dark_mode() if self.dark_mode_manager else False
        
        if dark_mode:
            app_style = """
                QMainWindow {
                    background-color: #212121;
                }
                QTabWidget::pane {
                    border: none;
                    background-color: #2d2d2d;
                    border-radius: 10px;
                    margin-top: -1px;
                }
                QTabBar::tab {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: none;
                    padding: 10px 20px;
                    margin: 0 2px;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    font-size: 13px;
                    min-width: 150px;
                }
                QTabBar::tab:selected {
                    background-color: #3d3d3d;
                    color: #ff9500;
                    border-bottom: 2px solid #ff9500;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #353535;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-bottom: 1px solid #424242;
                }
                QMenuBar::item {
                    padding: 8px 15px;
                    background-color: transparent;
                    color: #e0e0e0;
                }
                QMenuBar::item:selected {
                    background-color: #3d3d3d;
                    color: #ff9500;
                    border-radius: 5px;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #424242;
                    border-radius: 5px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 3px;
                }
                QMenu::item:selected {
                    background-color: #3d3d3d;
                    color: #ff9500;
                }
                QScrollBar:vertical {
                    border: none;
                    background-color: #2d2d2d;
                    width: 10px;
                    margin: 0;
                }
                QScrollBar::handle:vertical {
                    background-color: #424242;
                    border-radius: 5px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #ff9500;
                }
                QScrollBar:horizontal {
                    border: none;
                    background-color: #2d2d2d;
                    height: 10px;
                    margin: 0;
                }
                QScrollBar::handle:horizontal {
                    background-color: #424242;
                    border-radius: 5px;
                    min-width: 20px;
                }
                QScrollBar::handle:horizontal:hover {
                    background-color: #ff9500;
                }
            """
        else:
            app_style = """
                QMainWindow {
                    background-color: #f8f9fa;
                }
                QTabWidget::pane {
                    border: none;
                    background-color: #ffffff;
                    border-radius: 10px;
                    margin-top: -1px;
                }
                QTabBar::tab {
                    background-color: #f8f9fa;
                    color: #495057;
                    border: none;
                    padding: 10px 20px;
                    margin: 0 2px;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    font-size: 13px;
                    min-width: 150px;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                    color: #007bff;
                    border-bottom: 2px solid #007bff;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #e9ecef;
                    color: #212529;
                }
                QMenuBar {
                    background-color: #f8f9fa;
                    border-bottom: 1px solid #dee2e6;
                }
                QMenuBar::item {
                    padding: 8px 15px;
                    background-color: transparent;
                    color: #495057;
                }
                QMenuBar::item:selected {
                    background-color: #e9ecef;
                    color: #007bff;
                    border-radius: 5px;
                }
                QMenu {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 3px;
                }
                QMenu::item:selected {
                    background-color: #e9ecef;
                    color: #007bff;
                }
                QScrollBar:vertical {
                    border: none;
                    background-color: #f8f9fa;
                    width: 10px;
                    margin: 0;
                }
                QScrollBar::handle:vertical {
                    background-color: #adb5bd;
                    border-radius: 5px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #007bff;
                }
                QScrollBar:horizontal {
                    border: none;
                    background-color: #f8f9fa;
                    height: 10px;
                    margin: 0;
                }
                QScrollBar::handle:horizontal {
                    background-color: #adb5bd;
                    border-radius: 5px;
                    min-width: 20px;
                }
                QScrollBar::handle:horizontal:hover {
                    background-color: #007bff;
                }
            """
        
        # Apply the stylesheet to the entire application
        self.setStyleSheet(app_style)
        
        # Update all tabs' URL bar styles
        for tab_id, tab in self.tabs_dict.items():
            tab.update_url_bar_style(dark_mode)
            
        # Update the browser layout
        if hasattr(self, 'browser_layout'):
            self.browser_layout.update_button_style()

    def toggle_ad_blocker_from_toolbar(self):
        """Handle ad blocker toggle"""
        self.ad_blocker_enabled = not self.ad_blocker_enabled
        self.servo_thread.ad_blocker_enabled = self.ad_blocker_enabled
        
        # Show notification in current tab
        current_tab = self.browser_layout.get_tabs().currentWidget()
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
                </style>
                <script>
                    setTimeout(function() {{
                        window.history.back();
                    }}, 2000);
                </script>
            </head>
            <body>
                <div class="notification">
                    <h2>Ad Blocker Status Changed</h2>
                    <p>Ad blocker is now <strong>{'enabled' if self.ad_blocker_enabled else 'disabled'}</strong></p>
                </div>
            </body>
            </html>
            """
            current_tab.web_view.setHtml(notification_html)

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
        new_tab.bookmark_manager = self.bookmark_manager  # Set bookmark manager for initial tab
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
        
        # Add Security menu
        security_menu = menu_bar.addMenu("Security")
        
        # Add Phishing Detection toggle action
        phishing_action = QAction("Phishing Detection", self)
        phishing_action.setCheckable(True)
        phishing_action.setChecked(self.phishing_detection_enabled)
        phishing_action.triggered.connect(self.toggle_phishing_detection)
        security_menu.addAction(phishing_action)
        
        # Add Ad Blocker toggle action
        adblock_action = QAction("Ad Blocker", self)
        adblock_action.setCheckable(True)
        adblock_action.setChecked(self.ad_blocker_enabled)
        adblock_action.triggered.connect(self.toggle_ad_blocker)
        security_menu.addAction(adblock_action)
        
        # Add Dark Mode toggle action
        dark_mode_action = QAction("Dark Mode", self)
        dark_mode_action.setCheckable(True)
        dark_mode_action.setChecked(self.dark_mode_manager.is_dark_mode())
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        security_menu.addAction(dark_mode_action)
        
        # Rest of the existing menu items...
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
        """Set the default search engine for all tabs"""
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
        new_tab.bookmark_manager = self.bookmark_manager  # Use the global bookmark manager
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

    def toggle_proxy(self):
        """Launch VPN client in a new terminal window"""
        try:
            vpn_script = os.path.join(os.getcwd(), "test_vpn.py")
            if os.name == 'nt':  # For Windows
                subprocess.Popen(
                    ['start', 'cmd', '/k', 'python', vpn_script],
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:  # For Unix-like systems
                terminals = [
                    ['x-terminal-emulator', '-e'],
                    ['gnome-terminal', '--'],
                    ['konsole', '-e'],
                    ['xterm', '-e']
                ]
                for terminal in terminals:
                    try:
                        subprocess.Popen(terminal + ['python', vpn_script])
                        break
                    except FileNotFoundError:
                        continue
            
            # Update button state
            if hasattr(self, 'proxy_button'):
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

    def update_adblock_filters(self):
        try:
            self.servo_thread.ad_blocker.load_filters()
            QMessageBox.information(self, "Success", "Ad blocker filter lists updated successfully!")
            self.reload_current_page()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update ad blocker filters: {str(e)}")

    def toggle_ad_blocker(self, tab):
        """Toggle ad blocker state and update UI"""
        self.ad_blocker_enabled = not self.ad_blocker_enabled
        print(f"Ad blocker {'enabled' if self.ad_blocker_enabled else 'disabled'}")
        
        # Update the start page if we're on it
        if tab.current_url == "about:start":
            self.update_starting_screen(tab)
        else:
            # Show notification about the change
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
                </style>
                <script>
                    setTimeout(function() {{
                        window.history.back();
                    }}, 2000);
                </script>
            </head>
            <body>
                <div class="notification">
                    <h2>Ad Blocker Status Changed</h2>
                    <p>Ad blocker is now <strong>{'enabled' if self.ad_blocker_enabled else 'disabled'}</strong></p>
                </div>
            </body>
            </html>
            """
            tab.web_view.setHtml(notification_html)
            self.browser_layout.get_tabs().setTabText(self.browser_layout.get_tabs().currentIndex(), "Notification")
        
        # Update the ad blocker state in the ServoThread
        self.servo_thread.ad_blocker_enabled = self.ad_blocker_enabled

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

    def toggle_dark_mode(self):
        """Toggle dark mode on/off"""
        if hasattr(self, 'dark_mode_manager') and self.dark_mode_manager:
            self.dark_mode_manager.toggle_dark_mode()
            # Update the dark mode button text
            if hasattr(self, 'dark_mode_btn'):
                self.dark_mode_btn.setText(f"Dark Mode: {'On' if self.dark_mode_manager.is_dark_mode() else 'Off'}")
                self.dark_mode_btn.setChecked(self.dark_mode_manager.is_dark_mode())

    def toggle_phishing_detection(self):
        """Toggle phishing detection and update UI"""
        self.phishing_detection_enabled = not self.phishing_detection_enabled
        print(f"Phishing detection {'enabled' if self.phishing_detection_enabled else 'disabled'}")
        
        # Show notification in current tab
        current_tab = self.browser_layout.get_tabs().currentWidget()
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
                    <div class="status-icon">{'🛡️' if self.phishing_detection_enabled else '🚫'}</div>
                    <h2>Phishing Detection {self.phishing_detection_enabled and 'Enabled' or 'Disabled'}</h2>
                    <p>{'Protecting you from suspicious websites' if self.phishing_detection_enabled else 'Protection is turned off'}</p>
                </div>
            </body>
            </html>
            """
            current_tab.web_view.setHtml(notification_html)
            self.browser_layout.get_tabs().setTabText(
                self.browser_layout.get_tabs().currentIndex(),
                "Notification"
            )

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
            elif input_text == "about:toggle-adblocker" and self.parent_renderer:
                print("Processing about:toggle-adblocker")
                self.parent_renderer.toggle_ad_blocker(self)
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

            # Check for phishing only if enabled
            if self.phishing_detection_enabled:
                result = self.servo_thread.phishing_detector.analyze_url(url)
                if result["is_suspicious"]:
                    self.servo_thread.phishing_detected.emit(url, result)
                    return

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