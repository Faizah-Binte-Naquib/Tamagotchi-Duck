"""
Desktop Chat Widget - Chat interface with Stardew Valley-style chat bubbles
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
                                QPushButton, QLabel, QScrollArea, QFrame)
from PySide6.QtCore import Qt, QTimer, QPoint, QSize
from PySide6.QtGui import QFont, QPainter, QColor, QBrush, QPen, QMouseEvent, QPixmap
from chat.chat_service import ChatService


class ChatBubble(QWidget):
    """Individual chat bubble widget"""
    
    def __init__(self, message: str, is_user: bool = False, is_system: bool = False, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_user = is_user
        self.is_system = is_system
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Calculate size
        font = QFont()
        font.setPointSize(10)
        font.setFamily("Comic Sans MS")  # Whimsical font
        metrics = self.fontMetrics()
        text_rect = metrics.boundingRect(0, 0, 250, 0, Qt.TextWordWrap, message)
        
        self.setFixedSize(max(280, text_rect.width() + 30), text_rect.height() + 20)
    
    def paintEvent(self, event):
        """Draw the chat bubble"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Colors based on type
        if self.is_system:
            bg_color = QColor(255, 240, 200, 200)
            text_color = QColor(120, 80, 40)
            border_color = QColor(200, 150, 100)
        elif self.is_user:
            bg_color = QColor(150, 200, 255, 240)  # Light blue for user
            text_color = QColor(20, 60, 120)
            border_color = QColor(100, 150, 200)
        else:
            bg_color = QColor(255, 250, 200, 240)  # Light yellow for duck
            text_color = QColor(100, 80, 20)
            border_color = QColor(200, 180, 100)
        
        # Draw bubble with rounded corners
        bubble_rect = self.rect().adjusted(5, 5, -5, -5)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(bubble_rect, 12, 12)
        
        # Draw text
        painter.setPen(QPen(text_color))
        font = QFont()
        font.setPointSize(10)
        font.setFamily("Comic Sans MS")
        painter.setFont(font)
        painter.drawText(bubble_rect.adjusted(10, 5, -10, -5), Qt.TextWordWrap, self.message)


class DesktopChatWidget(QWidget):
    """Frameless window for chat interface with Stardew Valley vibes"""
    
    def __init__(self, chat_service: ChatService, game_logic, observer, desktop_duck=None, parent=None):
        super().__init__(parent)
        self.chat_service = chat_service
        self.game_logic = game_logic
        self.observer = observer
        self.desktop_duck_ref = desktop_duck  # Reference to desktop duck for chat bubbles
        
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        
        # Window properties - wider for chat bar
        self.setFixedSize(400, 500)
        
        # Drag properties
        self.drag_position = QPoint()
        self.is_dragging = False
        
        # Chat history
        self.chat_history = []
        self.bubbles = []  # List of chat bubble widgets
        
        # UI setup
        self.init_ui()
        
        # Get screen dimensions
        screen = self.screen().availableGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # Initial position (bottom right)
        self.move(screen.width() - 420, screen.height() - 520)
    
    def init_ui(self):
        """Initialize the chat UI with Stardew Valley style"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title with cute styling
        title = QLabel("💬 Chat with Duck")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_font.setFamily("Comic Sans MS")
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #5a4a3a; background: transparent;")
        layout.addWidget(title)
        
        # Chat history area with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(200, 180, 150, 100);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(150, 120, 90, 180);
                border-radius: 6px;
                min-height: 30px;
            }
        """)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(8)
        self.chat_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll_area.setWidget(self.chat_container)
        scroll_area.setMinimumHeight(350)
        layout.addWidget(scroll_area)
        
        # Input area - long chat bar style
        input_container = QFrame()
        input_container.setStyleSheet("background: transparent;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        
        # Long input bar
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 250);
                border: 3px solid #8b7355;
                border-radius: 15px;
                padding: 10px 15px;
                font-size: 11pt;
                font-family: 'Comic Sans MS';
                color: #3a2a1a;
            }
            QLineEdit:focus {
                border: 3px solid #6b5a4a;
                background-color: rgba(255, 255, 255, 255);
            }
        """)
        input_layout.addWidget(self.message_input, 4)  # Takes 4 parts
        
        # Send button - cute and whimsical
        self.send_btn = QPushButton("✨")
        self.send_btn.setFixedSize(50, 50)
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b9a5a;
                color: white;
                border: 3px solid #6b7a4a;
                border-radius: 25px;
                font-size: 18pt;
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
        input_layout.addWidget(self.send_btn, 1)  # Takes 1 part
        
        layout.addWidget(input_container)
        
        # Info label - subtle
        info_label = QLabel("💭 Keep messages about the duck!")
        info_font = QFont()
        info_font.setPointSize(9)
        info_font.setFamily("Comic Sans MS")
        info_font.setItalic(True)
        info_label.setFont(info_font)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #8b7355; background: transparent;")
        layout.addWidget(info_label)
    
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
    
    def send_message(self):
        """Send a chat message"""
        message = self.message_input.text().strip()
        if not message:
            return
        
        # Add user message as bubble in chat widget
        self.add_message_bubble(message, is_user=True)
        
        # Clear input
        self.message_input.clear()
        
        # Process message
        if self.game_logic.is_hatched():
            stats = self.game_logic.get_stats()
            response, is_on_topic = self.chat_service.process_message(
                user_message=message,
                duck_stats=stats,
                observer=self.observer
            )
            
            # Show response as bubble on the duck
            # We'll pass the desktop_duck reference through the widget
            if hasattr(self, 'desktop_duck_ref') and self.desktop_duck_ref:
                self.desktop_duck_ref.show_chat_bubble(response, duration=4000)
            
            # Also add to chat history for reference
            duck_name = self.game_logic.name or "Duck"
            self.add_message_bubble(f"{duck_name}: {response}", is_user=False)
            
            if not is_on_topic:
                # Show warning
                self.add_message_bubble("Please keep messages about the duck! 💭", is_system=True)
        else:
            self.add_message_bubble("Hatch the egg first! 🥚", is_system=True)
    
    def add_message_bubble(self, message: str, is_user: bool = False, is_system: bool = False):
        """Add a chat bubble to the display"""
        bubble = ChatBubble(message, is_user=is_user, is_system=is_system)
        self.bubbles.append(bubble)
        self.chat_layout.addWidget(bubble)
        
        # Auto-scroll to bottom
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scroll_bar = scroll_area.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())
        
        # Store in history
        self.chat_history.append({
            "message": message,
            "is_user": is_user,
            "is_system": is_system
        })
    
    def paintEvent(self, event):
        """Draw the chat widget background with Stardew Valley style"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw rounded rectangle background with gradient (warm, earthy tones)
        from PySide6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor(255, 245, 220, 245))  # Warm cream
        gradient.setColorAt(1, QColor(240, 230, 200, 245))  # Light beige
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(150, 120, 90), 3))  # Brown border
        painter.drawRoundedRect(5, 5, width - 10, height - 10, 15, 15)
        
        # Add subtle decorative border
        painter.setPen(QPen(QColor(200, 180, 150), 1))
        painter.drawRoundedRect(8, 8, width - 16, height - 16, 12, 12)
    
    def show_chat(self):
        """Show the chat window"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def hide_chat(self):
        """Hide the chat window"""
        self.hide()
    
    def set_position(self, x, y):
        """Set chat position on screen"""
        self.move(x, y)
    
    def get_position(self):
        """Get current position"""
        return self.pos()
