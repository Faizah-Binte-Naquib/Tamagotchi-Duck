"""
Desktop Personality Display Widget - Shows duck personality traits
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QMouseEvent
from personality.personality_engine import PersonalityEngine


class DesktopPersonalityDisplay(QWidget):
    """Frameless window for displaying personality traits"""
    
    def __init__(self, personality_engine: PersonalityEngine, parent=None):
        super().__init__(parent)
        self.personality_engine = personality_engine
        
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        
        # Window properties
        self.setFixedSize(250, 300)
        
        # Drag properties
        self.drag_position = QPoint()
        self.is_dragging = False
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(2000)  # Update every 2 seconds
        
        # Get screen dimensions
        screen = self.screen().availableGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # Initial position (top left)
        self.move(20, 20)
    
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
    
    def update_display(self):
        """Update the personality display"""
        self.update()
    
    def paintEvent(self, event):
        """Draw the personality display"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background
        from PySide6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor(240, 240, 255, 240))
        gradient.setColorAt(1, QColor(250, 240, 255, 240))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(150, 100, 200), 2))
        painter.drawRoundedRect(5, 5, width - 10, height - 10, 12, 12)
        
        # Get personality
        personality = self.personality_engine.get_personality()
        
        # Title
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor(100, 50, 150)))
        painter.drawText(10, 25, "🎭 Personality")
        
        # Draw personality traits
        y_offset = 45
        bar_height = 15
        bar_width = 180
        bar_spacing = 25
        
        traits = [
            ("Playfulness", personality.get("playfulness", 0.5), QColor(255, 200, 0)),
            ("Independence", personality.get("independence", 0.5), QColor(100, 200, 255)),
            ("Social", personality.get("social", 0.5), QColor(255, 150, 200)),
        ]
        
        label_font = QFont()
        label_font.setPointSize(9)
        painter.setFont(label_font)
        
        for i, (label, value, color) in enumerate(traits):
            y = y_offset + i * bar_spacing
            
            # Label
            painter.setPen(QPen(Qt.black))
            painter.drawText(10, y + 12, f"{label}:")
            
            # Background bar
            bar_x = 100
            painter.setBrush(QBrush(QColor(220, 220, 220)))
            painter.setPen(QPen(QColor(180, 180, 180), 1))
            painter.drawRoundedRect(bar_x, y, bar_width, bar_height, 3, 3)
            
            # Value bar
            bar_fill_width = int((value / 1.0) * bar_width)
            if bar_fill_width > 0:
                bar_gradient = QLinearGradient(bar_x, y, bar_x + bar_fill_width, y)
                bar_gradient.setColorAt(0, color.lighter(120))
                bar_gradient.setColorAt(1, color)
                painter.setBrush(QBrush(bar_gradient))
                painter.setPen(QPen(Qt.NoPen))
                painter.drawRoundedRect(bar_x, y, bar_fill_width, bar_height, 3, 3)
            
            # Value text
            painter.setPen(QPen(Qt.black))
            painter.drawText(bar_x + bar_width + 5, y + 12, f"{int(value * 100)}%")
        
        # Preferences
        preferences = personality.get("preferences", {})
        pref_y = y_offset + len(traits) * bar_spacing + 10
        
        pref_font = QFont()
        pref_font.setPointSize(8)
        pref_font.setBold(True)
        painter.setFont(pref_font)
        painter.setPen(QPen(QColor(100, 50, 150)))
        painter.drawText(10, pref_y, "Preferences:")
        
        pref_font.setBold(False)
        painter.setFont(pref_font)
        painter.setPen(QPen(Qt.black))
        
        favorite = preferences.get("favorite_activity", "eating")
        preferred_time = preferences.get("preferred_time", "afternoon")
        
        painter.drawText(10, pref_y + 18, f"Favorite: {favorite}")
        painter.drawText(10, pref_y + 33, f"Time: {preferred_time}")
        
        # Quirks
        quirks = personality.get("quirks", [])
        if quirks:
            quirks_y = pref_y + 55
            quirks_font = QFont()
            quirks_font.setPointSize(8)
            quirks_font.setBold(True)
            painter.setFont(quirks_font)
            painter.setPen(QPen(QColor(100, 50, 150)))
            painter.drawText(10, quirks_y, "Quirks:")
            
            quirks_font.setBold(False)
            painter.setFont(quirks_font)
            painter.setPen(QPen(Qt.black))
            
            for i, quirk in enumerate(quirks[:2]):  # Show first 2 quirks
                painter.drawText(10, quirks_y + 15 + i * 15, f"• {quirk[:30]}")
    
    def show_display(self):
        """Show the personality display window"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def hide_display(self):
        """Hide the personality display window"""
        self.hide()
    
    def set_position(self, x, y):
        """Set display position on screen"""
        self.move(x, y)
    
    def get_position(self):
        """Get current position"""
        return self.pos()
