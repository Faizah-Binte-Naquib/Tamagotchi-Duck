"""
Main Menu Widgets - Duck/Egg box and Item menu widgets for the main menu
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QPoint, QMimeData, QRect
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QMouseEvent, QDrag, QPixmap
from desktop_duck import DesktopDuckWindow
import os


class DuckEggBox(QWidget):
    """Box in main menu showing egg or duck - draggable to desktop"""
    
    SPRITE_SHEET_PATH = os.path.join(os.path.dirname(__file__), "images", "ducky_spritesheet.png")
    SPRITE_SIZE = 32
    
    def __init__(self, game_logic, parent=None):
        super().__init__(parent)
        self.game_logic = game_logic
        self.setFixedSize(120, 120)
        self.setAcceptDrops(False)
        
        # Load sprite sheet
        self.sprite_sheet = None
        self.load_sprite_sheet()
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fff5e6, stop:1 #f5e6d3);
                border: 3px solid #8b7355;
                border-radius: 10px;
            }
        """)
    
    def load_sprite_sheet(self):
        """Load the sprite sheet image"""
        if os.path.exists(self.SPRITE_SHEET_PATH):
            self.sprite_sheet = QPixmap(self.SPRITE_SHEET_PATH)
            if self.sprite_sheet.isNull():
                self.sprite_sheet = None
        else:
            self.sprite_sheet = None
    
    def paintEvent(self, event):
        """Draw egg or duck in the box"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw egg or duck
        if self.game_logic.is_hatched():
            # Draw duck sprite (idle_bounce - happy idle)
            if self.sprite_sheet and not self.sprite_sheet.isNull():
                # Use idle_bounce animation (row 2, frame 0)
                sprite_rect = QRect(0, self.SPRITE_SIZE * 2, self.SPRITE_SIZE, self.SPRITE_SIZE)
                # Scale to fit box (120x120, so scale sprite up)
                target_rect = QRect(20, 20, 80, 80)
                painter.drawPixmap(target_rect, self.sprite_sheet, sprite_rect)
            else:
                # Fallback to emoji
                font = QFont()
                font.setPointSize(60)
                font.setFamily("Segoe UI Emoji")
                painter.setFont(font)
                painter.setPen(QPen(Qt.black))
                painter.drawText(QRect(0, 0, width, height), Qt.AlignCenter, "🦆")
        else:
            # Draw egg
            font = QFont()
            font.setPointSize(60)
            font.setFamily("Segoe UI Emoji")
            painter.setFont(font)
            painter.setPen(QPen(Qt.black))
            painter.drawText(QRect(0, 0, width, height), Qt.AlignCenter, "🥚")
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press - start drag"""
        if event.button() == Qt.LeftButton and self.game_logic.is_hatched():
            # Only allow dragging if hatched
            self.drag_start_pos = event.position().toPoint()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move - create drag"""
        if not hasattr(self, 'drag_start_pos'):
            return
        
        if (event.buttons() == Qt.LeftButton and 
            (event.position().toPoint() - self.drag_start_pos).manhattanLength() > 10):
            # Store drop position before drag
            self.drop_pos = event.globalPosition().toPoint()
            
            # Start drag
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText("duck")
            drag.setMimeData(mime_data)
            
            # Create pixmap for drag
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint())
            
            # Execute drag
            result = drag.exec(Qt.MoveAction)
            
            # After drag completes, show duck on desktop
            if result == Qt.MoveAction and hasattr(self, 'drop_pos'):
                # Find parent window to call show_duck_on_desktop
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'show_duck_on_desktop'):
                        parent.show_duck_on_desktop(self.drop_pos.x(), self.drop_pos.y())
                        break
                    parent = parent.parent()
                delattr(self, 'drop_pos')
            
            delattr(self, 'drag_start_pos')


class ItemMenuWidget(QWidget):
    """Item menu showing draggable items (pond, grass, house)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fff5e6, stop:1 #f5e6d3);
                border: 3px solid #8b7355;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("📦 Item Menu")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_font.setFamily("Comic Sans MS")
        title.setFont(title_font)
        title.setStyleSheet("color: #5a4a3a; background: transparent;")
        layout.addWidget(title)
        
        # Items row
        items_layout = QHBoxLayout()
        items_layout.setSpacing(15)
        
        # Create draggable item widgets (using images instead of emojis)
        self.pond_item = DraggableItemIcon("Pond", "pond")
        self.grass_item = DraggableItemIcon("Grass", "grass")
        self.house_item = DraggableItemIcon("House", "house")
        
        items_layout.addWidget(self.pond_item)
        items_layout.addWidget(self.grass_item)
        items_layout.addWidget(self.house_item)
        items_layout.addStretch()
        
        layout.addLayout(items_layout)
        layout.addStretch()


class DraggableItemIcon(QWidget):
    """Draggable item icon in the item menu - uses images instead of emojis"""
    
    # Image paths - images folder is at project root (same level as this file)
    IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
    
    def __init__(self, name, item_type, parent=None):
        super().__init__(parent)
        self.name = name
        self.item_type = item_type
        self.setFixedSize(80, 100)
        
        # Load image for this item (downsized for icon)
        self.icon_image = None
        self.load_icon_image()
        
        self.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 150);
                border: 2px solid #8b7355;
                border-radius: 8px;
            }
            QWidget:hover {
                background: rgba(255, 255, 255, 200);
                border: 2px solid #9b8365;
            }
        """)
    
    def load_icon_image(self):
        """Load and downsize the item image for icon display"""
        image_map = {
            "pond": "Pixel_Pond.png",
            "grass": "Pixel_Grass.png",
            "house": "Pixel_House.png"
        }
        
        image_file = image_map.get(self.item_type)
        if image_file:
            image_path = os.path.join(self.IMAGE_DIR, image_file)
            if os.path.exists(image_path):
                # Load image and scale down to icon size (60x60)
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # Scale to fit icon area (60x60, leaving space for name)
                    self.icon_image = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
    def paintEvent(self, event):
        """Draw the item icon"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        width = self.width()
        height = self.height()
        
        # Draw image if available, otherwise fallback to emoji
        if self.icon_image and not self.icon_image.isNull():
            # Center the image in the icon area
            image_x = (width - self.icon_image.width()) // 2
            image_y = 10
            painter.drawPixmap(image_x, image_y, self.icon_image)
        else:
            # Fallback to emoji if image not found
            emoji_map = {"pond": "💧", "grass": "🌱", "house": "🏠"}
            emoji = emoji_map.get(self.item_type, "❓")
            font = QFont()
            font.setPointSize(40)
            font.setFamily("Segoe UI Emoji")
            painter.setFont(font)
            painter.setPen(QPen(Qt.black))
            painter.drawText(QRect(0, 10, width, 50), Qt.AlignCenter, emoji)
        
        # Draw name
        name_font = QFont()
        name_font.setPointSize(9)
        name_font.setBold(True)
        name_font.setFamily("Comic Sans MS")
        painter.setFont(name_font)
        painter.setPen(QPen(QColor(80, 60, 40)))
        painter.drawText(QRect(0, 70, width, 30), Qt.AlignCenter, self.name)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press - start drag"""
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.position().toPoint()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move - create drag"""
        if not hasattr(self, 'drag_start_pos'):
            return
        
        if (event.buttons() == Qt.LeftButton and 
            (event.position().toPoint() - self.drag_start_pos).manhattanLength() > 10):
            # Start drag
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(f"item:{self.item_type}")
            drag.setMimeData(mime_data)
            
            # Create pixmap for drag
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint())
            
            # Execute drag
            drag.exec(Qt.MoveAction)
            delattr(self, 'drag_start_pos')
