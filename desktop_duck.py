"""
Desktop Duck Window - A frameless window that displays the duck on the desktop with sprite animations
"""
import random
import math
import os
from datetime import datetime
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QMouseEvent, QPixmap, QImage
from duck_tamagotchi import DuckState


class DesktopDuckWindow(QWidget):
    """Frameless window for the duck that lives on the desktop"""
    
    # Sprite sheet configuration
    SPRITE_SHEET_PATH = os.path.join(os.path.dirname(__file__), "images", "ducky_spritesheet.png")
    # Sprite dimensions: 32x32 pixels (Lucky the Duck asset)
    SPRITE_SIZE = 32
    SPRITE_ROWS = 4  # 4 animation rows
    SPRITE_COLS = 6  # Maximum columns (for walk animations with 6 frames)
    
    # Animation configurations - each row in the sprite sheet
    ANIMATIONS = {
        "idle_normal": {"row": 0, "frames": 2, "speed": 500},   # Row 0: 2 frames
        "walk_normal": {"row": 1, "frames": 6, "speed": 150},   # Row 1: 6 frames
        "idle_bounce": {"row": 2, "frames": 4, "speed": 300},   # Row 2: 4 frames
        "walk_bounce": {"row": 3, "frames": 6, "speed": 120},    # Row 3: 6 frames
    }
    
    def __init__(self, game_logic, desktop_items=None, chat_service=None, observer=None, parent=None):
        super().__init__(parent)
        self.game_logic = game_logic
        self.desktop_items = desktop_items or []  # List of desktop item windows
        self.chat_service = chat_service  # Chat service for processing messages
        self.observer = observer  # Observer for logging interactions
        self.sound_enabled = True  # Sound toggle state
        
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)  # No system background
        # Set stylesheet to ensure no background
        self.setStyleSheet("background: transparent;")
        
        # Window properties - size based on sprite (3x scale for better visibility)
        # Make window wider to accommodate chat bubble, taller for bubble above duck
        sprite_display_size = self.SPRITE_SIZE * 3  # 96 pixels (3x scale)
        # Window width: wider to fit chat bubbles (320px), height: sprite + bubble space
        self.setFixedSize(320, sprite_display_size + 100)  # 320x196 display (wider for bubbles)
        
        # Load sprite sheet
        self.sprite_sheet = None
        self.load_sprite_sheet()
        
        # Animation state
        self.current_animation = "idle_normal"
        self.animation_frame = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.start_animation("idle_normal")
        
        # Behavior states
        self.current_behavior = "idle"  # idle, waddling, standing, playing
        self.behavior_timer = 0
        self.behavior_duration = 0
        
        # Random walking properties
        self.walking = False
        self.walk_target_x = 0
        self.walk_target_y = 0
        self.walk_speed = 1.5  # pixels per update
        self.walk_timer = QTimer()
        self.walk_timer.timeout.connect(self.update_walking)
        self.walk_timer.start(50)  # Update every 50ms for smooth animation
        
        # Interaction check timer - check even when not walking
        self.interaction_timer = QTimer()
        self.interaction_timer.timeout.connect(self.check_item_interactions)
        self.interaction_timer.start(500)  # Check every 500ms for interactions
        
        # Drag properties
        self.drag_position = QPoint()
        self.is_dragging = False
        self.click_start_pos = None  # Track click position to distinguish click from drag
        
        # Direction tracking for sprite mirroring
        self.facing_right = True  # Default facing right
        self.last_x = 0  # Track last position to determine direction
        
        # Chat bubble (for responses)
        self.chat_bubble_text = None
        self.chat_bubble_timer = QTimer()
        self.chat_bubble_timer.setSingleShot(True)
        self.chat_bubble_timer.timeout.connect(self.clear_chat_bubble)
        
        # Chat input bubble (for user input)
        self.chat_input_widget = None  # Will be created when needed
        
        # Get screen dimensions
        screen = self.screen().availableGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # Initial position (center of screen)
        initial_x = screen.width() // 2 - 32
        initial_y = screen.height() // 2 - 32
        self.move(initial_x, initial_y)
        self.last_x = initial_x  # Initialize last position
        
        # Initialize behavior
        self.change_behavior()
    
    def load_sprite_sheet(self):
        """Load the sprite sheet image"""
        if os.path.exists(self.SPRITE_SHEET_PATH):
            self.sprite_sheet = QPixmap(self.SPRITE_SHEET_PATH)
            if self.sprite_sheet.isNull():
                print(f"Warning: Could not load sprite sheet from {self.SPRITE_SHEET_PATH}")
                self.sprite_sheet = None
        else:
            print(f"Warning: Sprite sheet not found at {self.SPRITE_SHEET_PATH}")
            self.sprite_sheet = None
    
    def start_animation(self, animation_name: str):
        """Start a specific animation"""
        if animation_name not in self.ANIMATIONS:
            animation_name = "idle_normal"
        
        self.current_animation = animation_name
        self.animation_frame = 0
        anim_config = self.ANIMATIONS[animation_name]
        self.animation_timer.start(anim_config["speed"])
    
    def update_animation(self):
        """Update animation frame"""
        if self.current_animation in self.ANIMATIONS:
            anim_config = self.ANIMATIONS[self.current_animation]
            self.animation_frame = (self.animation_frame + 1) % anim_config["frames"]
            self.update()
    
    def get_current_sprite_rect(self) -> QRect:
        """Get the source rectangle for the current sprite frame"""
        if not self.sprite_sheet or self.current_animation not in self.ANIMATIONS:
            return QRect(0, 0, self.SPRITE_SIZE, self.SPRITE_SIZE)
        
        anim_config = self.ANIMATIONS[self.current_animation]
        row = anim_config["row"]
        col = self.animation_frame
        
        x = col * self.SPRITE_SIZE
        y = row * self.SPRITE_SIZE
        
        return QRect(x, y, self.SPRITE_SIZE, self.SPRITE_SIZE)
    
    def determine_animation(self) -> str:
        """
        Determine which animation to play based on duck state.
        Only one animation plays at a time:
        - Walking → walk_normal
        - Happy (while walking) → walk_bounce
        - Happy (while idle) → idle_bounce
        - Idle → idle_normal or idle_bounce (randomly)
        """
        stats = self.game_logic.get_stats()
        state = stats['state']
        current_action = stats.get('current_action')
        is_happy = state == "happy" or stats.get('happiness', 50) > 70
        
        # If duck is walking/moving
        if self.walking or self.current_behavior == "waddling" or current_action == "swimming":
            # Walking: use walk_normal, or walk_bounce if happy
            if is_happy:
                return "walk_bounce"
            return "walk_normal"
        
        # If duck is idle (not walking)
        if current_action == "sleeping" or state in ["sick", "tired"]:
            # Sleeping/sick/tired: use idle_normal
            return "idle_normal"
        elif current_action == "eating":
            # Eating: use idle_bounce (happy eating)
            return "idle_bounce"
        elif is_happy or self.current_behavior == "playing":
            # Happy/playing: use idle_bounce
            return "idle_bounce"
        else:
            # Normal idle: randomly choose between idle_normal or idle_bounce
            if random.random() < 0.3:  # 30% chance for bounce
                return "idle_bounce"
            return "idle_normal"
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for dragging or chat input"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.click_start_pos = event.globalPosition().toPoint()  # Track click start position
            self.walking = False  # Stop walking when dragging
            self.current_behavior = "idle"
            self.start_animation("idle_normal")
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for dragging"""
        if self.is_dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        elif self.click_start_pos:
            # If mouse moved significantly, it's a drag, not a click
            move_distance = (event.globalPosition().toPoint() - self.click_start_pos).manhattanLength()
            if move_distance > 5:
                self.is_dragging = True
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release - check for item interaction or show chat"""
        if event.button() == Qt.LeftButton:
            # Check if this was a click (not a drag)
            if self.click_start_pos:
                click_distance = (event.globalPosition().toPoint() - self.click_start_pos).manhattanLength()
                if click_distance < 5:  # Small movement = click, not drag
                    # Show chat input bubble
                    self.show_chat_input()
                    self.is_dragging = False
                    self.click_start_pos = None
                    event.accept()
                    return
            
            self.is_dragging = False
            self.click_start_pos = None
            
            # Check if duck was dropped on an item
            duck_center = QPoint(self.x() + self.width() // 2, self.y() + self.height() // 2)
            for item in self.desktop_items:
                if item.contains_point(duck_center):
                    # Duck is over this item - interact!
                    if self.game_logic.interact_with_item(item.item_type):
                        self.stop_walking()  # Stop walking when interacting
                        self.current_behavior = "idle"
                    break
            
            # Change behavior after release
            self.change_behavior()
            event.accept()
    
    def change_behavior(self):
        """Randomly change duck behavior"""
        if self.is_dragging or self.game_logic.current_action:
            return
        
        behaviors = ["waddling", "standing", "playing", "idle"]
        weights = [0.5, 0.15, 0.15, 0.2]  # Waddling is most common (50% chance)
        
        self.current_behavior = random.choices(behaviors, weights=weights)[0]
        
        if self.current_behavior == "waddling":
            self.start_random_walk()
        else:
            self.stop_walking()
        
        # Update animation based on new behavior
        new_anim = self.determine_animation()
        self.start_animation(new_anim)
        
        # Random duration for this behavior (3-8 seconds)
        self.behavior_duration = random.randint(3000, 8000)
        self.behavior_timer = 0
    
    def start_random_walk(self):
        """Start walking to a random location - prefer horizontal movement"""
        if self.is_dragging or self.game_logic.current_action:
            return
        
        # Pick a random target location - prefer horizontal movement
        margin = 50
        current_y = self.y()
        
        # X: full range for horizontal movement
        self.walk_target_x = random.randint(margin, self.screen_width - self.width() - margin)
        
        # Y: limited vertical movement (only small changes, or keep similar Y)
        y_variation = random.randint(-100, 100)  # Small vertical variation
        self.walk_target_y = max(margin, min(current_y + y_variation, 
                                            self.screen_height - self.height() - margin))
        
        self.walking = True
        self.current_behavior = "waddling"
        self.start_animation(self.determine_animation())
    
    def stop_walking(self):
        """Stop walking"""
        self.walking = False
        self.start_animation(self.determine_animation())
    
    def update_walking(self):
        """Update walking position - move towards target"""
        # Don't walk if interacting with items
        if self.game_logic.current_action:
            self.stop_walking()
            return
        
        if self.walking and not self.is_dragging and not self.game_logic.current_action:
            current_x = self.x()
            current_y = self.y()
            
            # Calculate direction to target
            dx = self.walk_target_x - current_x
            dy = self.walk_target_y - current_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 5:  # Not at target yet
                # Prefer horizontal movement - reduce vertical movement
                move_x = (dx / distance) * self.walk_speed
                move_y = (dy / distance) * self.walk_speed * 0.3  # Much less vertical movement
                
                # Avoid pure vertical movement (directly up or down)
                if abs(dx) < 10:  # If mostly vertical, add horizontal component
                    move_x = self.walk_speed * (1 if random.random() > 0.5 else -1)
                
                new_x = current_x + move_x
                new_y = current_y + move_y
                
                # Update facing direction based on movement
                if new_x > current_x:
                    self.facing_right = True
                elif new_x < current_x:
                    self.facing_right = False
                # If moving vertically only, keep current facing direction
                
                # Keep within screen bounds
                new_x = max(0, min(new_x, self.screen_width - self.width()))
                new_y = max(0, min(new_y, self.screen_height - self.height()))
                
                self.move(int(new_x), int(new_y))
                self.last_x = int(new_x)  # Update last position
                
                # Check for item interactions while walking
                self.check_item_interactions()
                
                # Update duck state to walking
                if not self.game_logic.current_action:
                    self.game_logic.state = DuckState.WALKING
                
                # Update animation if needed - ensure walking animation is playing
                new_anim = self.determine_animation()
                if new_anim != self.current_animation:
                    self.start_animation(new_anim)
                
                # Trigger repaint to update sprite direction
                self.update()
            else:
                # Reached target, stop walking
                self.stop_walking()
                if self.current_behavior == "waddling":
                    self.current_behavior = "standing"
        elif not self.game_logic.current_action and not self.is_dragging:
            # Return to idle if not walking
            if self.game_logic.state == DuckState.WALKING and not self.walking:
                self.game_logic.state = DuckState.IDLE
                self.start_animation(self.determine_animation())
    
    def check_item_interactions(self):
        """Check if duck is over a desktop item and interact - continuous interaction"""
        if not self.game_logic.is_hatched():
            return
        
        duck_center = QPoint(self.x() + self.width() // 2, self.y() + self.height() // 2)
        
        for item in self.desktop_items:
            if item.contains_point(duck_center):
                # Duck is over this item - interact!
                # If already interacting with this item, continue the interaction
                if self.game_logic.current_action and self.game_logic.current_action in ["eating", "swimming", "sleeping"]:
                    # Continue existing interaction - update stats periodically
                    self.continue_item_interaction(item.item_type)
                else:
                    # Start new interaction
                    if self.game_logic.interact_with_item(item.item_type):
                        self.stop_walking()  # Stop walking when interacting
                        self.current_behavior = "idle"
                        self.start_animation(self.determine_animation())
                return
        else:
            # Duck is not over any item - stop interaction if it was interacting
            if self.game_logic.current_action in ["eating", "swimming", "sleeping"]:
                self.game_logic.complete_action()
                self.current_behavior = "idle"
                self.start_animation(self.determine_animation())
    
    def continue_item_interaction(self, item_type):
        """Continue interaction with item - periodic stat updates"""
        # Update stats every few seconds while on item
        now = datetime.now()
        if not hasattr(self, 'last_interaction_update'):
            self.last_interaction_update = now
        
        # Update every 2 seconds while on item
        if (now - self.last_interaction_update).total_seconds() >= 2.0:
            self.last_interaction_update = now
            
            if item_type == "grass":
                # Continue eating - fill hunger gradually
                self.game_logic.hunger = min(self.game_logic.MAX_STAT, self.game_logic.hunger + 5)
                self.game_logic.happiness = min(self.game_logic.MAX_STAT, self.game_logic.happiness + 2)
            elif item_type == "pond":
                # Continue swimming - increase happiness and cleanliness
                self.game_logic.happiness = min(self.game_logic.MAX_STAT, self.game_logic.happiness + 3)
                self.game_logic.cleanliness = min(self.game_logic.MAX_STAT, self.game_logic.cleanliness + 2)
                self.game_logic.energy = max(self.game_logic.MIN_STAT, self.game_logic.energy - 1)
            elif item_type == "house":
                # Continue sleeping - restore energy
                self.game_logic.energy = min(self.game_logic.MAX_STAT, self.game_logic.energy + 10)
            
            # Update animation to reflect current action
            self.start_animation(self.determine_animation())
            
            # Force UI update by triggering a repaint
            self.update()
    
    def play_random_sound(self):
        """Play a random duck sound (quack)"""
        if self.is_dragging or self.game_logic.current_action:
            return
        
        # Random chance to play sound (30% chance)
        if random.random() < 0.3:
            pass  # Sound can be added with QSoundEffect if sound files are available
    
    def set_desktop_items(self, items):
        """Update the list of desktop items"""
        self.desktop_items = items
    
    def show_chat_bubble(self, text: str, duration: int = 3000):
        """Show a chat bubble above the duck"""
        self.chat_bubble_text = text
        self.chat_bubble_timer.start(duration)
        self.update()
    
    def clear_chat_bubble(self):
        """Clear the chat bubble"""
        self.chat_bubble_text = None
        self.update()
    
    def show_chat_input(self):
        """Show chat input thought bubble when duck is clicked"""
        if not self.game_logic.is_hatched():
            return
        
        if not self.chat_service or not self.observer:
            # Show message that chat is not available
            self.show_chat_bubble("Chat not available. Set up Ollama!", duration=3000)
            return
        
        # Create or show chat input widget
        if not self.chat_input_widget:
            from chat.chat_input_bubble import ChatInputBubble
            self.chat_input_widget = ChatInputBubble(self)
            self.chat_input_widget.set_chat_service(self.chat_service, self.observer, self.game_logic)
        
        # Position input bubble above duck
        duck_x = self.x()
        duck_y = self.y()
        bubble_x = duck_x - 150  # Center bubble above duck
        bubble_y = duck_y - 120  # Above the duck
        
        # Keep within screen bounds
        screen = self.screen().availableGeometry()
        bubble_x = max(10, min(bubble_x, screen.width() - 320))
        bubble_y = max(10, min(bubble_y, screen.height() - 100))
        
        self.chat_input_widget.move(bubble_x, bubble_y)
        self.chat_input_widget.show()
        self.chat_input_widget.raise_()
        self.chat_input_widget.activateWindow()
        self.chat_input_widget.message_input.setFocus()
    
    def paintEvent(self, event):
        """Draw the duck with sprite animations"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Update animation based on current state
        new_anim = self.determine_animation()
        if new_anim != self.current_animation:
            self.start_animation(new_anim)
        
        # Position sprite at bottom of window, centered horizontally
        sprite_height = self.SPRITE_SIZE * 3  # 96 pixels (3x scale)
        sprite_y = height - sprite_height  # Position at bottom
        sprite_x = (width - sprite_height) // 2  # Center sprite horizontally
        
        # Draw sprite if available - NO background, just the sprite
        if self.sprite_sheet and not self.sprite_sheet.isNull():
            sprite_rect = self.get_current_sprite_rect()
            # Scale sprite to fit (3x size: 32x32 sprite → 96x96 display)
            target_rect = QRect(sprite_x, sprite_y, sprite_height, sprite_height)
            
            # Use smooth scaling for better quality
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # Mirror sprite if facing left
            if not self.facing_right:
                # Flip horizontally by transforming the painter
                painter.save()
                # Translate to sprite position, scale with negative x
                painter.translate(sprite_x + sprite_height, sprite_y)
                painter.scale(-1, 1)
                painter.drawPixmap(QRect(0, 0, sprite_height, sprite_height), self.sprite_sheet, sprite_rect)
                painter.restore()
            else:
                # Draw normally when facing right
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.drawPixmap(target_rect, self.sprite_sheet, sprite_rect)
        else:
            # Fallback: Draw cute placeholder with Stardew Valley style
            self.draw_placeholder_duck(painter, width, height, sprite_y)
        
        # Draw chat bubble if active (above the duck)
        if self.chat_bubble_text:
            self.draw_chat_bubble(painter, width, height)
        
        # Name label removed - no longer displayed
    
    def draw_placeholder_duck(self, painter: QPainter, width: int, height: int, sprite_y: int = None):
        """Draw a cute placeholder duck when sprite sheet is not available"""
        if sprite_y is None:
            sprite_y = height - self.SPRITE_SIZE * 3
        
        stats = self.game_logic.get_stats()
        state = stats['state']
        
        sprite_height = self.SPRITE_SIZE * 3  # 96 pixels (3x scale)
        
        # Background color based on state (Stardew Valley palette)
        color_map = {
            "sick": QColor(180, 180, 180, 220),
            "hungry": QColor(255, 200, 150, 220),
            "tired": QColor(200, 200, 255, 220),
            "happy": QColor(255, 240, 150, 220),
        }
        bg_color = color_map.get(state, QColor(255, 220, 100, 220))
        
        # Draw rounded rectangle background for sprite area
        from PySide6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, sprite_y, 0, sprite_y + sprite_height)
        gradient.setColorAt(0, bg_color.lighter(110))
        gradient.setColorAt(1, bg_color)
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(120, 100, 80), 3))
        painter.drawRoundedRect(5, sprite_y + 5, sprite_height - 10, sprite_height - 10, 20, 20)
        
        # Draw duck emoji/text
        font = QFont()
        font.setPointSize(40)
        font.setFamily("Segoe UI Emoji")
        painter.setFont(font)
        painter.setPen(QPen(Qt.black))
        painter.drawText(QRect(0, sprite_y, sprite_height, sprite_height), Qt.AlignCenter, "🦆")
    
    def draw_chat_bubble(self, painter: QPainter, width: int, height: int):
        """Draw a chat bubble above the duck - dynamically sized based on text"""
        if not self.chat_bubble_text:
            return
        
        # Calculate bubble size dynamically based on text
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setFamily("Comic Sans MS")
        painter.setFont(font)
        
        # Measure text to determine bubble size
        # Use wider max width to allow text to spread horizontally
        max_text_width = width - 40  # Use full window width minus padding
        text_rect = painter.fontMetrics().boundingRect(
            0, 0, max_text_width, 0,
            Qt.TextWordWrap | Qt.AlignCenter,
            self.chat_bubble_text
        )
        
        # Calculate bubble dimensions with padding
        # Make bubble wider (increase width, keep height dynamic)
        padding = 20
        # Bubble can use most of the window width (window is now 320px wide)duck
        bubble_width = min(width - 20, max(250, text_rect.width() + padding * 2))
        bubble_height = max(50, text_rect.height() + padding)  # Height stays dynamic based on text
        
        # Position bubble at top of window, centered
        bubble_x = (width - bubble_width) // 2
        bubble_y = 10  # Top of window, above the duck sprite
        
        # Draw bubble background (Stardew Valley style)
        bubble_rect = QRect(bubble_x, bubble_y, bubble_width, bubble_height)
        painter.setBrush(QBrush(QColor(255, 250, 200, 250)))
        painter.setPen(QPen(QColor(200, 180, 100), 3))
        painter.drawRoundedRect(bubble_rect, 15, 15)
        
        # Draw text
        painter.setPen(QPen(QColor(100, 80, 20)))
        painter.drawText(bubble_rect.adjusted(15, 12, -15, -12), Qt.TextWordWrap | Qt.AlignCenter, self.chat_bubble_text)
        
        # Draw small tail pointing down to duck
        tail_x = width // 2
        tail_y = bubble_y + bubble_height
        tail_points = [
            QPoint(tail_x - 10, tail_y),
            QPoint(tail_x, tail_y + 10),
            QPoint(tail_x + 10, tail_y),
        ]
        painter.setBrush(QBrush(QColor(255, 250, 200, 250)))
        painter.setPen(QPen(QColor(200, 180, 100), 3))
        painter.drawPolygon(tail_points)
    
    def draw_name_label(self, painter: QPainter, width: int, height: int, sprite_y: int = None):
        """Draw the duck's name label"""
        if sprite_y is None:
            sprite_y = height - self.SPRITE_SIZE * 2
        
        name_font = QFont()
        name_font.setPointSize(10)
        name_font.setBold(True)
        name_font.setFamily("Comic Sans MS")
        painter.setFont(name_font)
        
        name_rect = painter.fontMetrics().boundingRect(self.game_logic.name)
        name_x = (width - name_rect.width()) // 2
        name_y = sprite_y + self.SPRITE_SIZE * 2 + 5  # Just below the sprite
        
        # Cute background for name (Stardew Valley style)
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.setPen(QPen(QColor(150, 120, 90), 2))
        painter.drawRoundedRect(int(name_x) - 6, name_y - 12, int(name_rect.width()) + 12, 16, 6, 6)
        
        painter.setPen(QPen(QColor(80, 60, 40)))
        painter.drawText(int(name_x), name_y, self.game_logic.name)
    
    def update_duck(self):
        """Update duck appearance"""
        # Update animation based on state
        new_anim = self.determine_animation()
        if new_anim != self.current_animation:
            self.start_animation(new_anim)
        self.update()
    
    def set_position(self, x, y):
        """Set duck position on screen"""
        self.move(x, y)
    
    def get_position(self):
        """Get current position"""
        return self.pos()
    
    def show_duck(self):
        """Show the duck window"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def hide_duck(self):
        """Hide the duck window"""
        self.hide()
