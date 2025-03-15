from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QTextEdit
import os
import requests
# Import custom parsers
import html_parser
import css_parser
import javascript_parser
from urllib.parse import urljoin, urlparse


def complete_url(url):
    """Ensure URL has a scheme (http/https)"""
    if not urlparse(url).scheme:
        return "https://" + url
    return url

def render_page(html_content, base_url):
    """Render and process HTML content"""
    if not html_content:
        return "No content to display."

    base_url = complete_url(base_url)  # Ensure URL is complete
    processed_html = f"Rendering content from {base_url}\n\n" + html_content[:500]  # Limiting output size

    return processed_html


def get_url(path):
    """Convert a local file path to a file:// URL or return the same if it's already a web URL."""
    if path.startswith("http://") or path.startswith("https://"):
        return path  # Already a URL
    return f"file://{os.path.abspath(path)}"  # Convert local path to file:// URL

class CustomWebRenderer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Webpage Renderer")
        self.setGeometry(300, 100, 1200, 800)

        # Main widget and layout
        self.main_widget = QWidget()
        self.layout = QVBoxLayout()

        # Address bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter file path or URL and press Enter...")
        self.url_bar.returnPressed.connect(self.load_page)
        self.layout.addWidget(self.url_bar)

        # Output Display
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.layout.addWidget(self.output_display)

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_page)
        self.layout.addWidget(self.refresh_button)

        # Set layout and central widget
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

    def format_url(self, url_or_path):
        """Ensures the URL is properly formatted."""
        url_or_path = url_or_path.strip()
        
        if os.path.exists(url_or_path):
            return get_url(url_or_path)  # Convert to file:// URL

        # Add https:// if it's a web address missing scheme
        if not url_or_path.startswith(("http://", "https://")) and "." in url_or_path:
            url_or_path = "https://" + url_or_path
        
        return url_or_path

    def load_page(self):
        url_or_path = self.format_url(self.url_bar.text())

        if url_or_path.startswith("file://"):
            try:
                with open(url_or_path[7:], 'r', encoding='utf-8') as file:
                    html_content = file.read()
                base_url = url_or_path
            except Exception as e:
                self.output_display.setText(f"Error loading file: {e}")
                return
        else:
            try:
                response = requests.get(url_or_path, timeout=5)
                response.raise_for_status()
                html_content = response.text
                base_url = url_or_path
            except requests.RequestException as e:
                self.output_display.setText(f"Failed to load URL: {e}")
                return

        # Process the content
        rendered_content = self.process_content(html_content, base_url)
        self.output_display.setHtml(rendered_content)

    def process_content(self, html_content, base_url):
        """
        Processes HTML content by applying CSS and executing JavaScript.
        """
        try:
            # Step 1: Parse HTML
            html_structure = html_parser.parse_html(html_content)

            # Step 2: Apply CSS Styles
            styled_structure = css_parser.apply_css(html_structure, base_url)

            # Step 3: Execute JavaScript (if needed)
            try:
                final_output = javascript_parser.execute_js(styled_structure, base_url)
            except AttributeError:
                final_output = styled_structure  # Skip JS execution if function isn't defined

            return final_output
        except Exception as e:
            return f"<b>Error:</b> {str(e)}"

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = CustomWebRenderer()
    window.show()
    sys.exit(app.exec_())
