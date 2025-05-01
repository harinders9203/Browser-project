import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QListWidget, QLineEdit, 
                           QLabel, QTabWidget, QMessageBox, QMenu, QDialog,
                           QInputDialog, QFileDialog, QAction)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
import json
from bookmarks import BookmarkManager
from history import BrowserHistoryProcessor

class BookmarkHistoryManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bookmark & History Manager")
        self.setMinimumSize(800, 600)
        
        # Initialize managers
        self.bookmark_manager = BookmarkManager()
        self.history_manager = BrowserHistoryProcessor("./browser_data/history.json")
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search bookmarks and history...")
        self.search_input.textChanged.connect(self.search_items)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create bookmarks tab
        self.bookmarks_tab = QWidget()
        bookmarks_layout = QVBoxLayout(self.bookmarks_tab)
        self.bookmarks_list = QListWidget()
        self.bookmarks_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmarks_list.customContextMenuRequested.connect(self.show_bookmark_context_menu)
        bookmarks_layout.addWidget(self.bookmarks_list)
        self.tabs.addTab(self.bookmarks_tab, "Bookmarks")
        
        # Create history tab
        self.history_tab = QWidget()
        history_layout = QVBoxLayout(self.history_tab)
        self.history_list = QListWidget()
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self.show_history_context_menu)
        history_layout.addWidget(self.history_list)
        self.tabs.addTab(self.history_tab, "History")
        
        # Create toolbar
        self.create_toolbar()
        
        # Load data
        self.load_bookmarks()
        self.load_history()
    
    def create_toolbar(self):
        toolbar = self.addToolBar("Actions")
        
        # Export action
        export_action = QAction("Export", self)
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)
        
        # Import action
        import_action = QAction("Import", self)
        import_action.triggered.connect(self.import_data)
        toolbar.addAction(import_action)
        
        # Clear history action
        clear_history_action = QAction("Clear History", self)
        clear_history_action.triggered.connect(self.clear_history)
        toolbar.addAction(clear_history_action)
    
    def load_bookmarks(self):
        self.bookmarks_list.clear()
        bookmarks = self.bookmark_manager.get_bookmarks()
        for bookmark in bookmarks:
            item = f"{bookmark['title']} ({bookmark['url']})"
            self.bookmarks_list.addItem(item)
    
    def load_history(self):
        self.history_list.clear()
        history = self.history_manager.history
        for entry in history:
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            item = f"{timestamp} - {entry['title']} ({entry['url']})"
            self.history_list.addItem(item)
    
    def search_items(self):
        search_text = self.search_input.text().lower()
        
        # Search in bookmarks
        for i in range(self.bookmarks_list.count()):
            item = self.bookmarks_list.item(i)
            item.setHidden(search_text not in item.text().lower())
        
        # Search in history
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            item.setHidden(search_text not in item.text().lower())
    
    def show_bookmark_context_menu(self, position):
        menu = QMenu()
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        open_action = menu.addAction("Open in Browser")
        
        action = menu.exec_(self.bookmarks_list.mapToGlobal(position))
        if action == edit_action:
            self.edit_bookmark()
        elif action == delete_action:
            self.delete_bookmark()
        elif action == open_action:
            self.open_bookmark()
    
    def show_history_context_menu(self, position):
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        open_action = menu.addAction("Open in Browser")
        
        action = menu.exec_(self.history_list.mapToGlobal(position))
        if action == delete_action:
            self.delete_history_entry()
        elif action == open_action:
            self.open_history_entry()
    
    def edit_bookmark(self):
        current_item = self.bookmarks_list.currentItem()
        if not current_item:
            return
        
        # Extract current title and URL
        text = current_item.text()
        title = text.split(' (')[0]
        url = text.split(' (')[1][:-1]
        
        # Get new values
        new_title, ok1 = QInputDialog.getText(self, "Edit Bookmark", "Title:", text=title)
        new_url, ok2 = QInputDialog.getText(self, "Edit Bookmark", "URL:", text=url)
        
        if ok1 and ok2:
            # Remove old bookmark and add new one
            self.bookmark_manager.remove_bookmark(url)
            self.bookmark_manager.add_bookmark(new_title, new_url)
            self.load_bookmarks()
    
    def delete_bookmark(self):
        current_item = self.bookmarks_list.currentItem()
        if not current_item:
            return
        
        text = current_item.text()
        url = text.split(' (')[1][:-1]
        
        reply = QMessageBox.question(self, "Delete Bookmark",
                                   "Are you sure you want to delete this bookmark?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.bookmark_manager.remove_bookmark(url)
            self.load_bookmarks()
    
    def open_bookmark(self):
        current_item = self.bookmarks_list.currentItem()
        if not current_item:
            return
        
        text = current_item.text()
        url = text.split(' (')[1][:-1]
        # TODO: Implement opening in browser
    
    def delete_history_entry(self):
        current_item = self.history_list.currentItem()
        if not current_item:
            return
        
        text = current_item.text()
        url = text.split(' (')[1][:-1]
        
        reply = QMessageBox.question(self, "Delete History Entry",
                                   "Are you sure you want to delete this history entry?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Remove the entry from history
            self.history_manager.history = [entry for entry in self.history_manager.history if entry['url'] != url]
            self.history_manager.save_history()
            self.load_history()
    
    def open_history_entry(self):
        current_item = self.history_list.currentItem()
        if not current_item:
            return
        
        text = current_item.text()
        url = text.split(' (')[1][:-1]
        # TODO: Implement opening in browser
    
    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "JSON Files (*.json)")
        if file_path:
            data = {
                'bookmarks': self.bookmark_manager.get_bookmarks(),
                'history': self.history_manager.history
            }
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
    
    def import_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Data", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Import bookmarks
                for bookmark in data.get('bookmarks', []):
                    self.bookmark_manager.add_bookmark(bookmark['title'], bookmark['url'])
                
                # Import history
                for entry in data.get('history', []):
                    self.history_manager.record_visit(entry['url'], entry['title'], entry['timestamp'])
                
                self.load_bookmarks()
                self.load_history()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import data: {str(e)}")
    
    def clear_history(self):
        reply = QMessageBox.question(self, "Clear History",
                                   "Are you sure you want to clear all history?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.history_manager.clear_history()
            self.load_history()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BookmarkHistoryManager()
    window.show()
    sys.exit(app.exec_()) 