from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import os
import json
import shutil

class BackgroundChanger(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Background Changer")
        self.setMinimumSize(400, 300)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Create image preview label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(300, 200)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        layout.addWidget(self.image_label)
        
        # Create change button
        self.change_button = QPushButton("Change Background")
        self.change_button.clicked.connect(self.change_background)
        layout.addWidget(self.change_button)
        
        # Load current background
        self.load_current_background()
        
    def load_current_background(self):
        # Try to load the current background from the browser data
        try:
            browser_data_dir = os.path.join(os.getcwd(), "browser_data")
            shortcuts_file = os.path.join(browser_data_dir, "shortcuts.json")
            
            if os.path.exists(shortcuts_file):
                with open(shortcuts_file, 'r') as f:
                    data = json.load(f)
                    background_image = data.get("background_image", "")
                    
                    if background_image.startswith("file:///"):
                        # Convert file URL to local path
                        local_path = background_image.replace("file:///", "")
                        if os.path.exists(local_path):
                            self.display_image(local_path)
                            return
            
            # If no background found, show default message
            self.image_label.setText("No background image set")
        except Exception as e:
            print(f"Error loading current background: {e}")
            self.image_label.setText("Error loading background")
    
    def change_background(self):
        # Open file dialog to select new image
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Background Image",
            os.path.expanduser("~"),
            "Image Files (*.jpg *.jpeg *.png *.gif *.bmp);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # Create images directory if it doesn't exist
            images_dir = os.path.join(os.getcwd(), "images")
            os.makedirs(images_dir, exist_ok=True)
            
            # Copy the selected image to the images directory
            new_image_path = os.path.join(images_dir, "img.jpg")
            shutil.copy2(file_path, new_image_path)
            
            # Convert to file URL
            file_url = f"file:///{new_image_path.replace('\\', '/')}"
            
            # Update the shortcuts.json file
            browser_data_dir = os.path.join(os.getcwd(), "browser_data")
            os.makedirs(browser_data_dir, exist_ok=True)
            
            shortcuts_file = os.path.join(browser_data_dir, "shortcuts.json")
            data = {}
            
            if os.path.exists(shortcuts_file):
                with open(shortcuts_file, 'r') as f:
                    data = json.load(f)
            
            data["background_image"] = file_url
            
            with open(shortcuts_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Display the new image
            self.display_image(new_image_path)
            
            QMessageBox.information(
                self,
                "Success",
                "Background image updated successfully!",
                QMessageBox.Ok
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to set background image:\n{str(e)}",
                QMessageBox.Ok
            )
    
    def display_image(self, image_path):
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale the image to fit the label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("Invalid image file")
        except Exception as e:
            print(f"Error displaying image: {e}")
            self.image_label.setText("Error displaying image")

if __name__ == '__main__':
    app = QApplication([])
    window = BackgroundChanger()
    window.show()
    app.exec_() 