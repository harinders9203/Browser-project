import json
import os
from pathlib import Path
from PyQt5.QtWidgets import QMenu, QAction, QInputDialog
from PyQt5.QtCore import Qt

class BookmarkManager:
    def __init__(self):
        # Create browser_data directory if it doesn't exist
        self.browser_data_dir = Path("browser_data")
        self.browser_data_dir.mkdir(exist_ok=True)
        
        # Set bookmarks file path
        self.bookmarks_file = self.browser_data_dir / "bookmarks.json"
        self.bookmarks = self._load_bookmarks()

    def _load_bookmarks(self):
        if self.bookmarks_file.exists():
            try:
                with open(self.bookmarks_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def _save_bookmarks(self):
        with open(self.bookmarks_file, 'w') as f:
            json.dump(self.bookmarks, f, indent=2)

    def add_bookmark(self, url, title):
        if not any(b['url'] == url for b in self.bookmarks):
            self.bookmarks.append({
                'url': url,
                'title': title
            })
            self._save_bookmarks()

    def remove_bookmark(self, url):
        self.bookmarks = [b for b in self.bookmarks if b['url'] != url]
        self._save_bookmarks()

    def get_bookmarks(self):
        return self.bookmarks

    def is_bookmarked(self, url):
        return any(b['url'] == url for b in self.bookmarks)

    def create_bookmark_menu(self, parent, current_tab):
        menu = QMenu("Bookmarks", parent)
        
        if not self.bookmarks:
            no_bookmarks = QAction("No bookmarks yet", menu)
            no_bookmarks.setEnabled(False)
            menu.addAction(no_bookmarks)
        else:
            for bookmark in self.bookmarks:
                action = QAction(bookmark['title'], menu)
                action.triggered.connect(lambda checked, url=bookmark['url']: current_tab.setUrl(QUrl(url)))
                menu.addAction(action)
            
            menu.addSeparator()
            clear_action = QAction("Clear All Bookmarks", menu)
            clear_action.triggered.connect(self.clear_all_bookmarks)
            menu.addAction(clear_action)
        
        return menu

    def clear_all_bookmarks(self):
        self.bookmarks = []
        self._save_bookmarks()

    def show_manage_bookmarks_page(self, tab):
        """Show the bookmarks management page"""
        bookmark_items = ""
        for bookmark in self.bookmarks:
            bookmark_items += f"""
                <div class="bookmark-item">
                    <div>
                        <div class="bookmark-title">{bookmark['title']}</div>
                        <div class="bookmark-url" onclick="window.location.href='{bookmark['url']}'">{bookmark['url']}</div>
                    </div>
                </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Manage Bookmarks</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: {'#212121' if hasattr(tab, 'dark_mode_manager') and tab.dark_mode_manager.is_dark_mode() else '#ffffff'};
                    color: {'#e0e0e0' if hasattr(tab, 'dark_mode_manager') and tab.dark_mode_manager.is_dark_mode() else '#333333'};
                }}
                .bookmark-list {{
                    list-style: none;
                    padding: 0;
                }}
                .bookmark-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 15px;
                    margin: 10px 0;
                    background-color: {'#2d2d2d' if hasattr(tab, 'dark_mode_manager') and tab.dark_mode_manager.is_dark_mode() else '#f5f5f5'};
                    border-radius: 8px;
                }}
                .bookmark-title {{
                    font-weight: bold;
                    margin-right: 15px;
                }}
                .bookmark-url {{
                    color: {'#bb86fc' if hasattr(tab, 'dark_mode_manager') and tab.dark_mode_manager.is_dark_mode() else '#2196f3'};
                }}
                .bookmark-url:hover {{
                    text-decoration: underline;
                    cursor: pointer;
                }}
            </style>
        </head>
        <body>
            <h1>Manage Bookmarks</h1>
            <div class="bookmark-list">
                {bookmark_items}
            </div>
        </body>
        </html>
        """
        tab.web_view.setHtml(html) 