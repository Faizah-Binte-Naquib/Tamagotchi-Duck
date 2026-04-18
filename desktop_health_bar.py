"""
Desktop Health Bar Widget - A frameless window showing duck stats on the desktop
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QMouseEvent


class DesktopHealthBar(QWidget):
    """Frameless window for health bar that can be placed on desktop"""
    
    def __init__(self, game_logic, parent=None):
        super().__init__(parent)
        self.game_logic = game_logic
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        
        # Window properties - wider to fit emoji labels
        self.setFixedSize(220, 180)
        
        # Drag properties
        self.drag_position = QPoint()
        self.is_dragging = False
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # Update every second
        
        # Get screen dimensions for positioning
        screen = self.screen().availableGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # Initial position (top right)
        self.move(screen.width() - 240, 20)
    
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
    
    def update_stats(self):
        """Update the health bar display"""
        self.update()
    
    def paintEvent(self, event):
        """Draw the health bar"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Stardew Valley-style gradient background (warm, earthy)
        from PySide6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor(255, 245, 220, 245))  # Warm cream
        gradient.setColorAt(1, QColor(240, 230, 200, 245))  # Light beige
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(150, 120, 90), 3))  # Brown border
        painter.drawRoundedRect(5, 5, width - 10, height - 10, 15, 15)
        
        # Add subtle decorative border
        painter.setPen(QPen(QColor(200, 180, 150), 1))
        painter.drawRoundedRect(7, 7, width - 14, height - 14, 13, 13)
        
        if not self.game_logic.is_hatched():
            # Show egg status
            font = QFont()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(Qt.black))
            painter.drawText(10, 30, "🥚 Egg")
            return
        
        # Get stats
        stats = self.game_logic.get_stats()
        
        # Stardew Valley-style title with emoji
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_font.setFamily("Comic Sans MS")  # Whimsical font
        painter.setFont(title_font)
        painter.setPen(QPen(QColor(100, 50, 150)))
        painter.drawText(10, 20, f"🦆 {self.game_logic.name}")
        
        # Draw stat bars
        y_offset = 35
        bar_height = 12
        bar_width = 150
        bar_spacing = 18
        
        stats_to_show = [
            ("🍽️ Hunger", stats['hunger'], QColor(255, 165, 0)),
            ("😊 Happiness", stats['happiness'], QColor(255, 215, 0)),
            ("❤️ Health", stats['health'], QColor(0, 200, 0)),
            ("⚡ Energy", stats['energy'], QColor(0, 150, 255)),
            ("✨ Clean", stats['cleanliness'], QColor(173, 216, 230)),
        ]
        
        label_font = QFont()
        label_font.setPointSize(8)
        label_font.setFamily("Comic Sans MS")  # Whimsical font
        painter.setFont(label_font)
        
        for i, (label, value, color) in enumerate(stats_to_show):
            y = y_offset + i * bar_spacing
            
            # Label
            painter.setPen(QPen(Qt.black))
            painter.drawText(10, y + 10, f"{label}:")
            
            # Background bar with cute style
            bar_x = 85
            painter.setBrush(QBrush(QColor(220, 220, 220)))
            painter.setPen(QPen(QColor(180, 180, 180), 1))
            painter.drawRoundedRect(bar_x, y, bar_width, bar_height, 4, 4)
            
            # Value bar with gradient
            bar_fill_width = int((value / 100) * bar_width)
            if bar_fill_width > 0:
                from PySide6.QtGui import QLinearGradient
                bar_gradient = QLinearGradient(bar_x, y, bar_x + bar_fill_width, y)
                bar_gradient.setColorAt(0, color.lighter(120))
                bar_gradient.setColorAt(1, color)
                painter.setBrush(QBrush(bar_gradient))
                painter.setPen(QPen(Qt.NoPen))
                painter.drawRoundedRect(bar_x, y, bar_fill_width, bar_height, 4, 4)
            
            # Value text
            painter.setPen(QPen(Qt.black))
            painter.drawText(bar_x + bar_width + 5, y + 10, f"{int(value)}%")
        
        # State
        state_font = QFont()
        state_font.setPointSize(8)
        state_font.setBold(True)
        painter.setFont(state_font)
        state_text = stats.get('state', 'idle').title()
        if stats.get('current_action'):
            state_text += f" - {stats['current_action'].title()}"
        painter.setPen(QPen(Qt.darkBlue))
        painter.drawText(10, height - 10, f"State: {state_text}")
    
    def show_bar(self):
        """Show the health bar window"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def hide_bar(self):
        """Hide the health bar window"""
        self.hide()
    
    def set_position(self, x, y):
        """Set health bar position on screen"""
        self.move(x, y)
    
    def get_position(self):
        """Get current position"""
        return self.pos()
