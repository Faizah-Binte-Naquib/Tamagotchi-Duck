"""
DuckMind - Main Application
An AI-powered desktop companion featuring a duck character that learns and evolves
"""
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QPushButton, QLabel, QProgressBar,
                                QMessageBox, QInputDialog, QGraphicsView, QGraphicsScene,
                                QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, QFrame)
from PySide6.QtCore import QTimer, Qt, QPointF, QRectF, QPoint, QMimeData
from PySide6.QtGui import QFont, QPainter, QColor, QBrush, QPen, QDrag, QPixmap, QMouseEvent
from duck_tamagotchi import DuckTamagotchi, DuckState, GameStage
from desktop_duck import DesktopDuckWindow
from desktop_items import DesktopItemWindow, create_desktop_item
from desktop_health_bar import DesktopHealthBar
from main_menu_widgets import DuckEggBox, ItemMenuWidget

# LLM and Personality system imports
from memory.vector_store import VectorStore
from llm.llm_service import LLMService
from llm.rag_service import RAGService
from personality.observer import Observer
from personality.personality_engine import PersonalityEngine
from personality.personality_display import DesktopPersonalityDisplay
from chat.topic_filter import TopicFilter
from chat.chat_service import ChatService
from chat.chat_widget import DesktopChatWidget
from config.llm_config import LLMConfig
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)


class DraggableItem(QGraphicsRectItem):
    """Base class for draggable items on the desktop"""
    
    def __init__(self, item_type, name, color, width=100, height=100):
        super().__init__(0, 0, width, height)
        self.item_type = item_type
        self.name = name
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.black, 2))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptDrops(True)
        
        # Add text label
        self.text_item = QGraphicsTextItem(name, self)
        self.text_item.setDefaultTextColor(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        self.text_item.setFont(font)
        # Center text
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos((width - text_rect.width()) / 2, (height - text_rect.height()) / 2)
    
    def contains_point(self, point):
        """Check if point is within this item"""
        return self.rect().contains(self.mapFromScene(point))


class DuckGraphicsItem(QGraphicsRectItem):
    """Draggable duck character"""
    
    def __init__(self, game_logic, scene):
        super().__init__(0, 0, 80, 80)
        self.game_logic = game_logic
        self.scene = scene
        self.setBrush(QBrush(QColor(255, 220, 0)))  # Yellow duck
        self.setPen(QPen(Qt.black, 2))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptDrops(False)
        self.is_dragging = False
        
        # Text label
        self.text_item = QGraphicsTextItem("🦆", self)
        font = QFont()
        font.setPointSize(30)
        self.text_item.setFont(font)
        self.text_item.setPos(15, 15)
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        self.is_dragging = True
        if not self.game_logic.current_action:
            self.game_logic.state = DuckState.WALKING
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release - check for item interaction"""
        self.is_dragging = False
        super().mouseReleaseEvent(event)
        
        # Check if duck is over an item
        duck_center = self.scenePos() + QPointF(40, 40)
        for item in self.scene.items_placed:
            item_rect = item.sceneBoundingRect()
            if item_rect.contains(duck_center):
                # Duck is over this item - interact!
                if self.game_logic.interact_with_item(item.item_type):
                    self.scene.show_interaction_feedback(item)
                break
        else:
            # Not over any item, return to idle
            if not self.game_logic.current_action:
                self.game_logic.state = DuckState.IDLE
    
    def update_appearance(self):
        """Update duck appearance based on state and animation"""
        stats = self.game_logic.get_stats()
        state = stats['state']
        frame = stats['animation_frame']
        current_action = stats.get('current_action')
        
        # Update color based on state
        if state == "sick":
            color = QColor(200, 200, 200)  # Gray
        elif state == "hungry":
            color = QColor(255, 200, 100)  # Light orange
        elif state == "tired":
            color = QColor(200, 200, 255)  # Light blue
        else:
            color = QColor(255, 220, 0)  # Yellow
        
        self.setBrush(QBrush(color))
        
        # Update text based on action and frame
        if current_action == "eating":
            self.text_item.setPlainText("🦆" if frame == 0 else "🦆\n↓")
        elif current_action == "swimming":
            self.text_item.setPlainText("🦆→" if frame == 0 else "←🦆")
        elif current_action == "sleeping":
            self.text_item.setPlainText("😴")
        elif state == "walking" or (not current_action and frame == 1):
            self.text_item.setPlainText("🦆\n👣")
        else:
            self.text_item.setPlainText("🦆")


class EggGraphicsItem(QGraphicsRectItem):
    """Egg display during incubation"""
    
    def __init__(self, game_logic):
        super().__init__(0, 0, 100, 120)
        self.game_logic = game_logic
        self.setBrush(QBrush(QColor(255, 255, 200)))  # Light yellow/white
        self.setPen(QPen(Qt.black, 2))
        
        # Text label
        self.text_item = QGraphicsTextItem("🥚", self)
        font = QFont()
        font.setPointSize(40)
        self.text_item.setFont(font)
        self.text_item.setPos(20, 30)
    
    def update_appearance(self):
        """Update egg appearance"""
        progress = self.game_logic.get_incubation_progress()
        # Could add visual feedback based on progress
        pass


class DesktopScene(QGraphicsScene):
    """Scene for displaying items (items can also be desktop windows later)"""
    
    def __init__(self, game_logic, parent=None):
        super().__init__(parent)
        self.game_logic = game_logic
        self.items_placed = []
        self.setSceneRect(0, 0, 1000, 700)
        self.setBackgroundBrush(QBrush(QColor(240, 248, 255)))  # Light blue background
    
    def add_item(self, item_type):
        """Add a new draggable item to the scene"""
        if item_type == "pond":
            item = DraggableItem("pond", "Pond\n💧", QColor(100, 150, 255), 120, 120)
        elif item_type == "grass":
            item = DraggableItem("grass", "Grass\n🌱", QColor(100, 200, 100), 120, 120)
        elif item_type == "house":
            item = DraggableItem("house", "House\n🏠", QColor(150, 100, 50), 120, 120)
        else:
            return None
        
        # Position new items in a row
        x = 200 + len(self.items_placed) * 150
        y = 50
        item.setPos(x, y)
        self.items_placed.append(item)
        self.addItem(item)
        return item


class TamagotchiWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.game_logic = DuckTamagotchi()
        self.desktop_duck = None  # Desktop duck window
        self.desktop_items = []  # List of desktop item windows - MUST be initialized before create_desktop_duck
        self.desktop_health_bar = None  # Desktop health bar window
        self.desktop_personality_display = None  # Personality display widget
        self.desktop_chat_widget = None  # Chat widget
        
        # Initialize LLM and personality system
        self._initialize_personality_system()
        
        self.init_ui()
        self.setup_timer()
        self.game_logic.load()  # Try to load saved game
        self.create_desktop_duck()  # Create desktop duck window (but don't show automatically)
        # Don't create desktop health bar and personality display - they're in the main menu now
        # Chat is now handled via thought bubble on duck click
        
    def init_ui(self):
        """Initialize the user interface with new rectangular menu layout"""
        self.setWindowTitle("DuckMind - AI Companion")
        self.setGeometry(100, 100, 600, 500)  # Rectangular menu window
        
        # Apply Stardew Valley style to main window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5e6d3;
            }
        """)
        
        # Central widget - rectangular menu
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Main menu panel - Stardew Valley style
        menu_panel = QWidget()
        menu_panel.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fff5e6, stop:1 #f5e6d3);
                border: 3px solid #8b7355;
                border-radius: 15px;
            }
        """)
        menu_layout = QVBoxLayout(menu_panel)
        menu_layout.setContentsMargins(15, 15, 15, 15)
        menu_layout.setSpacing(15)
        
        # Top section: Duck/Egg box (left) + Personality & Health info (right)
        top_section = QHBoxLayout()
        top_section.setSpacing(15)
        
        # Left: Duck/Egg box
        self.duck_egg_box = DuckEggBox(self.game_logic)
        top_section.addWidget(self.duck_egg_box)
        
        # Right: Personality and Health info
        info_section = QVBoxLayout()
        info_section.setSpacing(10)
        
        # Personality info
        personality_frame = QFrame()
        personality_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 150);
                border: 2px solid #8b7355;
                border-radius: 8px;
            }
        """)
        personality_layout = QVBoxLayout(personality_frame)
        personality_layout.setContentsMargins(10, 10, 10, 10)
        
        personality_title = QLabel("🎭 Personality")
        personality_title_font = QFont()
        personality_title_font.setPointSize(11)
        personality_title_font.setBold(True)
        personality_title_font.setFamily("Comic Sans MS")
        personality_title.setFont(personality_title_font)
        personality_title.setStyleSheet("color: #5a4a3a; background: transparent;")
        personality_layout.addWidget(personality_title)
        
        self.personality_info_label = QLabel("Not available yet")
        self.personality_info_label.setWordWrap(True)
        self.personality_info_label.setStyleSheet("color: #6b5a4a; background: transparent; font-size: 9pt;")
        personality_layout.addWidget(self.personality_info_label)
        
        info_section.addWidget(personality_frame)
        
        # Health info (compact stats)
        health_frame = QFrame()
        health_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 150);
                border: 2px solid #8b7355;
                border-radius: 8px;
            }
        """)
        health_layout = QVBoxLayout(health_frame)
        health_layout.setContentsMargins(10, 10, 10, 10)
        
        health_title = QLabel("❤️ Health")
        health_title_font = QFont()
        health_title_font.setPointSize(11)
        health_title_font.setBold(True)
        health_title_font.setFamily("Comic Sans MS")
        health_title.setFont(health_title_font)
        health_title.setStyleSheet("color: #5a4a3a; background: transparent;")
        health_layout.addWidget(health_title)
        
        # Compact health bars
        self.compact_health_bars = {}
        for stat_name in ["Hunger", "Happiness", "Health", "Energy", "Cleanliness"]:
            emoji_map = {"Hunger": "🍽️", "Happiness": "😊", "Health": "❤️", "Energy": "⚡", "Cleanliness": "✨"}
            emoji = emoji_map.get(stat_name, "")
            stat_layout = QHBoxLayout()
            
            label = QLabel(f"{emoji}")
            label.setFixedWidth(25)
            stat_layout.addWidget(label)
            
            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(100)
            bar.setValue(100)
            bar.setTextVisible(False)
            bar.setFixedHeight(12)
            bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #8b7355;
                    border-radius: 4px;
                    background-color: #e8d5c0;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #8b9a5a, stop:1 #6b7a4a);
                    border-radius: 3px;
                }
            """)
            stat_layout.addWidget(bar)
            health_layout.addLayout(stat_layout)
            self.compact_health_bars[stat_name] = bar
        
        info_section.addWidget(health_frame)
        
        top_section.addLayout(info_section)
        top_section.addStretch()
        
        menu_layout.addLayout(top_section)
        
        # Bottom section: Item Menu
        self.item_menu = ItemMenuWidget()
        menu_layout.addWidget(self.item_menu)
        
        # Connect item menu drag events
        self.item_menu.pond_item.mouseMoveEvent = lambda e: self.handle_item_drag(e, "pond", self.item_menu.pond_item)
        self.item_menu.grass_item.mouseMoveEvent = lambda e: self.handle_item_drag(e, "grass", self.item_menu.grass_item)
        self.item_menu.house_item.mouseMoveEvent = lambda e: self.handle_item_drag(e, "house", self.item_menu.house_item)
        
        # Add menu panel to main layout
        main_layout.addWidget(menu_panel)
        
        # Action buttons (compact row at bottom)
        buttons_row = QHBoxLayout()
        button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d4c4a8, stop:1 #c4b498);
                border: 3px solid #8b7355;
                border-radius: 10px;
                color: #3a2a1a;
                font-weight: bold;
                font-size: 9pt;
                font-family: 'Comic Sans MS';
                padding: 6px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e4d4b8, stop:1 #d4c4a8);
                border: 3px solid #9b8365;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c4b498, stop:1 #b4a488);
                border: 3px solid #7b6345;
            }
        """
        
        # Hatch button (for testing)
        self.hatch_btn = QPushButton("🥚 Hatch")
        self.hatch_btn.clicked.connect(self.hatch_egg)
        self.hatch_btn.setStyleSheet(button_style)
        buttons_row.addWidget(self.hatch_btn)
        
        # Rename button
        self.rename_btn = QPushButton("✏️ Rename")
        self.rename_btn.clicked.connect(self.rename_duck)
        self.rename_btn.setStyleSheet(button_style)
        buttons_row.addWidget(self.rename_btn)
        
        # Sound toggle button
        self.sound_enabled = True
        self.sound_btn = QPushButton("🔊 Sound")
        self.sound_btn.clicked.connect(self.toggle_sound)
        self.sound_btn.setStyleSheet(button_style)
        buttons_row.addWidget(self.sound_btn)
        
        buttons_row.addStretch()
        
        main_layout.addLayout(buttons_row)
        
        # Status message
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #5a7a3a;
                background: rgba(255, 255, 255, 150);
                border: 2px solid #8b7355;
                border-radius: 8px;
                padding: 5px;
                font-weight: bold;
                font-size: 9pt;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # Still create scene for compatibility but don't show it
        self.scene = DesktopScene(self.game_logic)
        
        # Update display
        self.update_display()
        
        # Setup interaction checking (for desktop duck with items)
        self.interaction_timer = QTimer()
        self.interaction_timer.timeout.connect(self.check_desktop_interactions)
        self.interaction_timer.start(1000)  # Check every second
    
    def handle_item_drag(self, event, item_type, widget):
        """Handle dragging items from menu to desktop"""
        if not hasattr(widget, 'drag_start_pos'):
            return
        
        if (event.buttons() == Qt.LeftButton and 
            (event.position().toPoint() - widget.drag_start_pos).manhattanLength() > 10):
            # Create desktop item at drop position
            screen = self.screen().availableGeometry()
            drop_x = event.globalPosition().x()
            drop_y = event.globalPosition().y()
            
            # Create desktop item
            item = create_desktop_item(item_type, drop_x, drop_y)
            if item:
                self.desktop_items.append(item)
                item.show_item()
                
                # Update desktop duck's item list
                if self.desktop_duck:
                    self.desktop_duck.set_desktop_items(self.desktop_items)
            
            delattr(widget, 'drag_start_pos')
        
    def create_stat_bar(self, name):
        """Create a stat progress bar with label - Stardew Valley style"""
        # Emoji mapping for stats
        emoji_map = {
            "Hunger": "🍽️",
            "Happiness": "😊",
            "Health": "❤️",
            "Energy": "⚡",
            "Cleanliness": "✨"
        }
        emoji = emoji_map.get(name, "")
        
        label = QLabel(f"{emoji} {name}:")
        label.setStyleSheet("""
            QLabel {
                color: #5a4a3a;
                background: transparent;
                font-weight: bold;
                font-size: 10pt;
            }
        """)
        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(100)
        bar.setValue(100)
        bar.setTextVisible(True)
        bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #8b7355;
                border-radius: 6px;
                text-align: center;
                background-color: #e8d5c0;
                color: #5a4a3a;
                font-weight: bold;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b9a5a, stop:1 #6b7a4a);
                border-radius: 4px;
            }
        """)
        return {'label': label, 'bar': bar}
    
    def setup_timer(self):
        """Setup timer for automatic updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_game)
        self.update_timer.start(1000)  # Update every second
        
    def update_game(self):
        """Update game state"""
        # Check for auto-hatch
        if not self.game_logic.is_hatched() and self.game_logic.should_auto_hatch():
            self.auto_hatch()
        
        self.game_logic.update()
        self.update_display()
        self.check_game_over()
    
    def auto_hatch(self):
        """Auto-hatch the egg when time is up"""
        if self.game_logic.hatch():
            # Ask for name
            name, ok = QInputDialog.getText(self, "Egg Hatched!", "Your egg has hatched!\nEnter duck name:", 
                                           text=self.game_logic.name)
            if ok and name.strip():
                self.game_logic.name = name.strip()
            else:
                self.game_logic.name = "Ducky"
            
            # Observe naming event
            if self.observer:
                self.observer.observe_naming_event(self.game_logic.name, self.game_logic.get_stats())
            
            # Create desktop duck window
            self.create_desktop_duck()
            # Show health bar when hatched
            self.create_desktop_health_bar()
            # Show personality display when hatched
            self.create_personality_display()
            # Generate initial personality if enough observations
            if self.personality_engine:
                self.personality_engine.generate_personality(
                    duck_stats=self.game_logic.get_stats(),
                    force_regenerate=False
                )
            self.show_status(f"{self.game_logic.name} has hatched! 🦆 Check your desktop!")
            self.update_display()
    
    def create_desktop_duck(self):
        """Create the desktop duck window - but don't show it automatically"""
        if self.game_logic.is_hatched():
            if self.desktop_duck:
                self.desktop_duck.hide_duck()
            self.desktop_duck = DesktopDuckWindow(
                self.game_logic, 
                self.desktop_items,
                chat_service=self.chat_service if hasattr(self, 'chat_service') else None,
                observer=self.observer if hasattr(self, 'observer') else None
            )
            # Pass sound state
            if hasattr(self, 'sound_enabled'):
                self.desktop_duck.sound_enabled = self.sound_enabled
            # Don't show automatically - only show when dragged from menu
            # self.desktop_duck.show_duck()
        else:
            # Hide duck if egg
            if self.desktop_duck:
                self.desktop_duck.hide_duck()
    
    def show_duck_on_desktop(self, x=None, y=None):
        """Show duck on desktop at specified position (called when dragged from menu)"""
        if self.desktop_duck and self.game_logic.is_hatched():
            if x is not None and y is not None:
                # Adjust position to center duck at drop point
                # Duck is now 96x196, so adjust accordingly
                self.desktop_duck.move(x - self.desktop_duck.width() // 2, 
                                      y - self.desktop_duck.height() // 2)
            else:
                # Center on screen if no position given
                screen = self.desktop_duck.screen().availableGeometry()
                self.desktop_duck.move(screen.width() // 2 - 32, screen.height() // 2 - 32)
            
            self.desktop_duck.show_duck()
            # Start duck walking
            if hasattr(self.desktop_duck, 'start_random_walk'):
                self.desktop_duck.start_random_walk()
    
    def _initialize_personality_system(self):
        """Initialize LLM and personality system components"""
        try:
            # Initialize vector store
            LLMConfig.ensure_vector_db_directory()
            vector_store = VectorStore(persist_directory=LLMConfig.get_vector_db_path())
            
            # Initialize LLM service
            llm_service = LLMService()
            
            # Initialize RAG service
            rag_service = RAGService(vector_store)
            
            # Initialize observer
            observer = Observer(vector_store)
            self.game_logic.observer = observer
            
            # Initialize personality engine
            personality_engine = PersonalityEngine(llm_service, rag_service)
            self.game_logic.personality_engine = personality_engine
            
            # Initialize topic filter
            topic_filter = TopicFilter(llm_service)
            
            # Initialize chat service
            chat_service = ChatService(llm_service, rag_service, personality_engine, topic_filter)
            
            # Store references
            self.vector_store = vector_store
            self.llm_service = llm_service
            self.rag_service = rag_service
            self.observer = observer
            self.personality_engine = personality_engine
            self.chat_service = chat_service
            
            logging.info("Personality system initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize personality system: {e}")
            logging.warning("Game will run without LLM features (personality and chat)")
            logging.info("To enable LLM features:")
            logging.info("  1. Install Ollama: https://ollama.ai")
            logging.info("  2. Run: ollama pull llama3.1:8b")
            logging.info("  3. Restart the application")
            # Set to None so we can check later
            self.personality_engine = None
            self.chat_service = None
            self.observer = None
            self.vector_store = None
            self.llm_service = None
            self.rag_service = None
    
    def create_desktop_health_bar(self):
        """Create the desktop health bar window"""
        if not self.desktop_health_bar:
            self.desktop_health_bar = DesktopHealthBar(self.game_logic)
        if self.game_logic.is_hatched():
            self.desktop_health_bar.show_bar()
        else:
            self.desktop_health_bar.hide_bar()
    
    def create_personality_display(self):
        """Create the desktop personality display window"""
        if not self.personality_engine:
            return
        
        if not self.desktop_personality_display:
            self.desktop_personality_display = DesktopPersonalityDisplay(self.personality_engine)
        if self.game_logic.is_hatched():
            self.desktop_personality_display.show_display()
        else:
            self.desktop_personality_display.hide_display()
    
    def toggle_personality_display(self):
        """Toggle personality display visibility"""
        if not self.desktop_personality_display:
            self.create_personality_display()
        
        if not self.desktop_personality_display:
            self.show_status("Personality system not available", error=True)
            return
        
        if self.desktop_personality_display.isVisible():
            self.desktop_personality_display.hide_display()
            self.personality_btn.setText("🎭 Show Personality")
        else:
            if self.game_logic.is_hatched():
                self.desktop_personality_display.show_display()
                self.personality_btn.setText("🎭 Hide Personality")
            else:
                self.show_status("Hatch the egg first! 🥚", error=True)
    
    def create_chat_widget(self):
        """Create the desktop chat widget - no longer used, chat is on duck click"""
        # Chat is now handled via thought bubble on duck click
        pass
    
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            self.sound_btn.setText("🔊 Sound On")
            self.show_status("Sound enabled 🔊")
        else:
            self.sound_btn.setText("🔇 Sound Off")
            self.show_status("Sound disabled 🔇")
        
        # Pass sound state to desktop duck if it exists
        if self.desktop_duck:
            self.desktop_duck.sound_enabled = self.sound_enabled
    
    def toggle_health_bar(self):
        """Toggle health bar visibility"""
        if not self.desktop_health_bar:
            self.create_desktop_health_bar()
        
        if self.desktop_health_bar.isVisible():
            self.desktop_health_bar.hide_bar()
            self.health_bar_btn.setText("📊 Show Health Bar")
        else:
            if self.game_logic.is_hatched():
                self.desktop_health_bar.show_bar()
                self.health_bar_btn.setText("📊 Hide Health Bar")
            else:
                self.show_status("Hatch the egg first! 🥚", error=True)
    
    def check_desktop_interactions(self):
        """Check if desktop duck should interact with items"""
        if not self.desktop_duck or not self.game_logic.is_hatched():
            return
        
        # Check if duck is near any items (could implement proximity detection)
        # For now, interactions happen when user drags duck to items
        pass
    
    def update_display(self):
        """Update all UI elements"""
        stats = self.game_logic.get_stats()
        
        # Update duck/egg box
        if hasattr(self, 'duck_egg_box'):
            self.duck_egg_box.update()
        
        # Update compact health bars - real-time updates
        if hasattr(self, 'compact_health_bars'):
            if self.game_logic.is_hatched():
                # Update all health bars with current stats
                self.compact_health_bars['Hunger'].setValue(int(stats['hunger']))
                self.compact_health_bars['Happiness'].setValue(int(stats['happiness']))
                self.compact_health_bars['Health'].setValue(int(stats['health']))
                self.compact_health_bars['Energy'].setValue(int(stats['energy']))
                self.compact_health_bars['Cleanliness'].setValue(int(stats['cleanliness']))
            else:
                # Show egg stats (all at 0 or hidden)
                for bar in self.compact_health_bars.values():
                    bar.setValue(0)
        
        # Update personality info - real-time updates
        if hasattr(self, 'personality_info_label'):
            if self.personality_engine:
                personality = self.personality_engine.get_personality()
                if personality:
                    # Get personality description or build from traits
                    description = personality.get('personality_description', '')
                    if description:
                        # Use the description if available
                        self.personality_info_label.setText(description)
                    else:
                        # Build description from traits
                        playfulness = personality.get('playfulness', 0.5)
                        independence = personality.get('independence', 0.5)
                        social = personality.get('social', 0.5)
                        
                        # Create readable description
                        traits_desc = []
                        if playfulness > 0.6:
                            traits_desc.append("playful")
                        elif playfulness < 0.4:
                            traits_desc.append("calm")
                        
                        if independence > 0.6:
                            traits_desc.append("independent")
                        elif independence < 0.4:
                            traits_desc.append("needy")
                        
                        if social > 0.6:
                            traits_desc.append("social")
                        elif social < 0.4:
                            traits_desc.append("reserved")
                        
                        if traits_desc:
                            trait_text = f"Traits: {', '.join(traits_desc)}"
                        else:
                            trait_text = "Balanced personality"
                        
                        self.personality_info_label.setText(trait_text)
                else:
                    self.personality_info_label.setText("Personality developing...")
            else:
                self.personality_info_label.setText("LLM not available")
        
        # Update hatch button
        if hasattr(self, 'hatch_btn'):
            if self.game_logic.is_hatched():
                self.hatch_btn.setEnabled(False)
            else:
                self.hatch_btn.setEnabled(True)
        
        # Update desktop duck display
        if self.desktop_duck:
            self.desktop_duck.update_duck()
        
        # Update desktop health bar
        if self.desktop_health_bar and self.desktop_health_bar.isVisible():
            self.desktop_health_bar.update_stats()
        
        # Update personality display
        if self.desktop_personality_display and self.desktop_personality_display.isVisible():
            self.desktop_personality_display.update_display()
        
        # Auto-save every 30 seconds
        if hasattr(self, 'save_counter'):
            self.save_counter += 1
            if self.save_counter >= 30:
                self.game_logic.save()
                self.save_counter = 0
        else:
            self.save_counter = 0
    
    def hatch_egg(self):
        """Hatch the egg (testing button)"""
        if self.game_logic.hatch():
            # Ask for name
            name, ok = QInputDialog.getText(self, "Name Your Duck", "Enter duck name:", 
                                           text=self.game_logic.name)
            if ok and name.strip():
                self.game_logic.name = name.strip()
            else:
                self.game_logic.name = "Ducky"
            
            # Observe naming event
            if self.observer:
                self.observer.observe_naming_event(self.game_logic.name, self.game_logic.get_stats())
            
            # Create desktop duck window
            self.create_desktop_duck()
            # Show health bar when hatched
            self.create_desktop_health_bar()
            # Show personality display when hatched
            self.create_personality_display()
            # Generate initial personality if enough observations
            if self.personality_engine:
                self.personality_engine.generate_personality(
                    duck_stats=self.game_logic.get_stats(),
                    force_regenerate=False
                )
            self.show_status(f"{self.game_logic.name} has hatched! 🦆 Check your desktop!")
            self.update_display()
    
    def add_item(self, item_type):
        """Add a new item to the desktop"""
        if not self.game_logic.is_hatched():
            self.show_status("Hatch the egg first! 🥚", error=True)
            return
        
        # Create desktop item window
        item = create_desktop_item(item_type)
        if item:
            self.desktop_items.append(item)
            item.show_item()
            
            # Update duck's item list
            if self.desktop_duck:
                self.desktop_duck.set_desktop_items(self.desktop_items)
            
            self.show_status(f"Added {item_type} to desktop! Drag duck to it to interact.")
    
    def rename_duck(self):
        """Rename the duck"""
        if not self.game_logic.is_hatched():
            self.show_status("Hatch the egg first! 🥚", error=True)
            return
        
        new_name, ok = QInputDialog.getText(self, "Rename Duck", "Enter new name:", 
                                           text=self.game_logic.name)
        if ok and new_name.strip():
            self.game_logic.name = new_name.strip()
            self.update_display()
            self.show_status(f"Duck renamed to {self.game_logic.name}!")
    
    def show_status(self, message, error=False):
        """Show status message"""
        self.status_label.setText(message)
        if error:
            self.status_label.setStyleSheet("color: red;")
        else:
            self.status_label.setStyleSheet("color: green;")
        
        # Clear message after 3 seconds
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))
    
    def check_game_over(self):
        """Check if duck has died"""
        if self.game_logic.is_dead():
            self.update_timer.stop()
            self.interaction_timer.stop()
            reply = QMessageBox.question(self, "Game Over", 
                                        f"{self.game_logic.name} has passed away...\n\nStart a new game?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                # Hide all desktop windows
                if self.desktop_duck:
                    self.desktop_duck.hide_duck()
                for item in self.desktop_items:
                    item.hide_item()
                if self.desktop_health_bar:
                    self.desktop_health_bar.hide_bar()
                
                self.game_logic = DuckTamagotchi()
                self.desktop_items = []
                self.scene = DesktopScene(self.game_logic)
                self.create_desktop_duck()
                self.create_desktop_health_bar()
                self.update_timer.start(1000)
                self.interaction_timer.start(1000)
                self.update_display()
            else:
                self.close()
    
    def closeEvent(self, event):
        """Save game when closing"""
        self.game_logic.save()
        if self.desktop_duck:
            self.desktop_duck.hide_duck()
        for item in self.desktop_items:
            item.hide_item()
        if self.desktop_health_bar:
            self.desktop_health_bar.hide_bar()
        if self.desktop_personality_display:
            self.desktop_personality_display.hide_display()
        if self.desktop_chat_widget:
            self.desktop_chat_widget.hide_chat()
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = TamagotchiWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
