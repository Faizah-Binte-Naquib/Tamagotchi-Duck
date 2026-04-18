"""
Chat Input Bubble - Thought bubble that appears above duck for chat input
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                                QPushButton, QLabel)
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QMouseEvent
from chat.chat_service import ChatService


class ChatInputBubble(QWidget):
    """Thought bubble widget for chat input - appears above duck when clicked"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chat_service = None
        self.observer = None
        self.game_logic = None
        
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Window properties
        self.setFixedSize(300, 100)
        
        # Drag properties
        self.drag_position = QPoint()
        self.is_dragging = False
        
        # UI setup
        self.init_ui()
    
    def init_ui(self):
        """Initialize the chat input UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        # Long input bar - Stardew Valley style
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 250);
                border: 3px solid #8b7355;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 11pt;
                font-family: 'Comic Sans MS';
                color: #3a2a1a;
            }
            QLineEdit:focus {
                border: 3px solid #6b5a4a;
                background-color: rgba(255, 255, 255, 255);
            }
        """)
        input_layout.addWidget(self.message_input, 4)
        
        # Send button
        self.send_btn = QPushButton("✨")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b9a5a;
                color: white;
                border: 3px solid #6b7a4a;
                border-radius: 20px;
                font-size: 16pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9baa6a;
                border: 3px solid #7b8a5a;
            }
            QPushButton:pressed {
                background-color: #7b8a4a;
            }
        """)
        input_layout.addWidget(self.send_btn, 1)
        
        layout.addLayout(input_layout)
        
        # Hint label
        hint = QLabel("💭 Click duck to chat!")
        hint_font = QFont()
        hint_font.setPointSize(8)
        hint_font.setFamily("Comic Sans MS")
        hint_font.setItalic(True)
        hint.setFont(hint_font)
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #8b7355; background: transparent;")
        layout.addWidget(hint)
    
    def set_chat_service(self, chat_service: ChatService, observer, game_logic):
        """Set the chat service and related components"""
        self.chat_service = chat_service
        self.observer = observer
        self.game_logic = game_logic
    
    def send_message(self):
        """Send a chat message"""
        message = self.message_input.text().strip()
        if not message:
            return
        
        # Clear input first
        self.message_input.clear()
        
        # Show "thinking..." message on duck
        if self.parent() and hasattr(self.parent(), 'show_chat_bubble'):
            self.parent().show_chat_bubble("💭 Thinking...", duration=2000)
        
        # Process message
        if self.game_logic and self.game_logic.is_hatched():
            stats = self.game_logic.get_stats()
            response, is_on_topic = self.chat_service.process_message(
                user_message=message,
                duck_stats=stats,
                observer=self.observer
            )
            
            # Show response as bubble on the duck (longer duration so user can read it)
            if self.parent() and hasattr(self.parent(), 'show_chat_bubble'):
                self.parent().show_chat_bubble(response, duration=6000)
            
            if not is_on_topic:
                # Show warning after a delay
                if self.parent() and hasattr(self.parent(), 'show_chat_bubble'):
                    QTimer.singleShot(6500, lambda: self.parent().show_chat_bubble("Please keep messages about the duck! 💭", duration=3000))
        else:
            if self.parent() and hasattr(self.parent(), 'show_chat_bubble'):
                self.parent().show_chat_bubble("Hatch the egg first! 🥚", duration=3000)
        
        # Hide input bubble after a short delay to let user see the response starts
        QTimer.singleShot(500, self.hide)
    
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
        """Draw the thought bubble background with Stardew Valley style"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw rounded rectangle background with gradient (warm, earthy tones)
        from PySide6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor(255, 250, 220, 250))  # Warm cream
        gradient.setColorAt(1, QColor(240, 230, 200, 250))  # Light beige
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(150, 120, 90), 3))  # Brown border
        painter.drawRoundedRect(5, 5, width - 10, height - 10, 15, 15)
        
        # Add subtle decorative border
        painter.setPen(QPen(QColor(200, 180, 150), 1))
        painter.drawRoundedRect(8, 8, width - 16, height - 16, 12, 12)
        
        # Draw thought bubble tail pointing down (towards duck)
        tail_points = [
            QPoint(width // 2 - 10, height - 5),
            QPoint(width // 2, height - 15),
            QPoint(width // 2 + 10, height - 5),
        ]
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(150, 120, 90), 3))
        painter.drawPolygon(tail_points)
