"""
Desktop Item Windows - Frameless windows for items that can be placed on the desktop
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QMouseEvent, QPixmap
import os


class DesktopItemWindow(QWidget):
    """Frameless window for items (pond, grass, house) that can be placed on desktop"""
    
    # Image directory - images folder is at project root (same level as this file)
    IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
    
    def __init__(self, item_type, name, emoji, color, width=120, height=120, parent=None):
        super().__init__(parent)
        self.item_type = item_type
        self.name = name
        self.emoji = emoji  # Fallback emoji
        self.color = color
        
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        # Enable transparency for transparent PNG backgrounds
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent;")
        
        # Window properties
        self.setFixedSize(width, height)
        
        # Drag properties
        self.drag_position = QPoint()
        self.is_dragging = False
        
        # Get screen dimensions for positioning
        screen = self.screen().availableGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # Initial position (scattered around screen)
        self.initial_x = 200
        self.initial_y = 200
        
        # Load full-size image and resize window to match original image size
        self.item_image = None
        self.original_image = None
        self.has_image = False
        self.load_item_image()
    
    def load_item_image(self):
        """Load the full-size item image - scale up if too small for duck"""
        image_map = {
            "pond": "Pixel_Pond.png",
            "grass": "Pixel_Grass.png",
            "house": "Pixel_House.png"
        }
        
        # Minimum sizes to accommodate 96x96 duck (with some margin)
        min_sizes = {
            "pond": (250, 250),
            "grass": (400, 200),
            "house": (200, 200)
        }
        
        image_file = image_map.get(self.item_type)
        if image_file:
            image_path = os.path.join(self.IMAGE_DIR, image_file)
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # Get minimum size for this item type
                    min_width, min_height = min_sizes.get(self.item_type, (200, 200))
                    
                    # Scale up if image is smaller than minimum
                    if pixmap.width() < min_width or pixmap.height() < min_height:
                        # Scale to at least minimum size, maintaining aspect ratio
                        scaled = pixmap.scaled(
                            min_width,
                            min_height,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        self.original_image = scaled
                        self.item_image = scaled
                    else:
                        # Use original size if it's already big enough
                        self.original_image = pixmap
                        self.item_image = pixmap
                    
                    self.has_image = True
                    
                    # Resize window to match image size (add space for name label if needed)
                    img_width = self.item_image.width()
                    img_height = self.item_image.height() + 25  # Add space for name label
                    self.setFixedSize(img_width, img_height)
                else:
                    self.original_image = None
                    self.item_image = None
                    self.has_image = False
            else:
                self.original_image = None
                self.item_image = None
                self.has_image = False
        else:
            self.original_image = None
            self.item_image = None
            self.has_image = False
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for dragging"""
        if self.is_dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            event.accept()
    
    def paintEvent(self, event):
        """Draw the item with transparent background if image is loaded"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        width = self.width()
        height = self.height()
        
        # Only draw background if no image (fallback mode with emoji)
        if not self.has_image or not self.item_image or self.item_image.isNull():
            # Draw Stardew Valley-style rounded rectangle background with gradient
            from PySide6.QtGui import QLinearGradient
            gradient = QLinearGradient(0, 0, width, height)
            # Warmer, more earthy tones
            base_color = self.color
            gradient.setColorAt(0, QColor(
                min(255, base_color.red() + 30),
                min(255, base_color.green() + 20),
                min(255, base_color.blue() + 10),
                240
            ))
            gradient.setColorAt(1, QColor(
                max(0, base_color.red() - 20),
                max(0, base_color.green() - 10),
                max(0, base_color.blue() - 5),
                240
            ))
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(120, 100, 80), 3))  # Brown border
            painter.drawRoundedRect(4, 4, width - 8, height - 8, 18, 18)  # More rounded
            
            # Add subtle inner border for depth
            painter.setPen(QPen(QColor(200, 180, 150), 1))
            painter.drawRoundedRect(6, 6, width - 12, height - 12, 16, 16)
            
            # Fallback to emoji if image not found
            font = QFont()
            font.setPointSize(50)
            painter.setFont(font)
            
            emoji_rect = painter.fontMetrics().boundingRect(self.emoji)
            emoji_x = (width - emoji_rect.width()) / 2
            emoji_y = height / 2 - 5
            painter.setPen(QPen(Qt.black))
            painter.drawText(int(emoji_x), int(emoji_y), self.emoji)
        else:
            # Draw image at original size with transparent background
            # Image is drawn at top, name label at bottom
            image_x = 0
            image_y = 0
            painter.drawPixmap(image_x, image_y, self.item_image)
        
        # Draw Stardew Valley-style name label with background (always show)
        name_font = QFont()
        name_font.setPointSize(10)
        name_font.setBold(True)
        name_font.setFamily("Comic Sans MS")  # Whimsical font
        painter.setFont(name_font)
        name_rect = painter.fontMetrics().boundingRect(self.name)
        name_x = (width - name_rect.width()) / 2
        name_y = height - 10
        
        # Cute background for name (Stardew Valley style)
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.setPen(QPen(QColor(150, 120, 90), 2))  # Brown border
        painter.drawRoundedRect(int(name_x) - 6, name_y - 12, int(name_rect.width()) + 12, 16, 6, 6)
        
        painter.setPen(QPen(QColor(80, 60, 40)))  # Dark brown text
        painter.drawText(int(name_x), name_y, self.name)
    
    def get_rect(self):
        """Get the item's rectangle in screen coordinates"""
        return QRect(self.pos().x(), self.pos().y(), self.width(), self.height())
    
    def contains_point(self, point):
        """Check if a point (in screen coordinates) is within this item"""
        rect = self.get_rect()
        return rect.contains(point)
    
    def show_item(self):
        """Show the item window"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def hide_item(self):
        """Hide the item window"""
        self.hide()
    
    def set_position(self, x, y):
        """Set item position on screen"""
        self.move(x, y)
    
    def get_position(self):
        """Get current position"""
        return self.pos()


def create_desktop_item(item_type, x=None, y=None):
    """Factory function to create desktop items - size will be set by image"""
    # Default sizes - increased to accommodate 96x96 duck (will be overridden by actual image size if image loads)
    default_sizes = {
        "pond": (250, 250),      # Increased from 180x180
        "grass": (400, 200),      # Increased from 300x120
        "house": (200, 200)       # Increased from 150x150
    }
    
    if item_type == "pond":
        width, height = default_sizes["pond"]
        item = DesktopItemWindow("pond", "Pond", "💧", QColor(100, 150, 255, 200), width, height)
        default_x, default_y = 300, 200
    elif item_type == "grass":
        width, height = default_sizes["grass"]
        item = DesktopItemWindow("grass", "Grass", "🌱", QColor(100, 200, 100, 200), width, height)
        default_x, default_y = 450, 200
    elif item_type == "house":
        width, height = default_sizes["house"]
        item = DesktopItemWindow("house", "House", "🏠", QColor(150, 100, 50, 200), width, height)
        default_x, default_y = 600, 200
    else:
        return None
    
    if x is None:
        x = default_x
    if y is None:
        y = default_y
    
    item.set_position(x, y)
    return item
