"""
DuckMind Game Logic
"""
import json
import os
from datetime import datetime, timedelta
from enum import Enum


class GameStage(Enum):
    """Game progression stages"""
    EGG = "egg"
    DUCK = "duck"


class DuckState(Enum):
    """Different states the duck can be in"""
    IDLE = "idle"
    WALKING = "walking"
    EATING = "eating"
    SWIMMING = "swimming"
    SLEEPING = "sleeping"
    HAPPY = "happy"
    HUNGRY = "hungry"
    TIRED = "tired"
    SICK = "sick"
    DIRTY = "dirty"


class DuckTamagotchi:
    """Main game logic for DuckMind"""
    
    MAX_STAT = 100
    MIN_STAT = 0
    INCUBATION_HOURS = 5  # 5 hours to hatch
    
    def __init__(self, name="Ducky"):
        self.stage = GameStage.EGG
        self.name = name
        self.hunger = 80
        self.happiness = 80
        self.health = 100
        self.energy = 80
        self.cleanliness = 80
        self.age = 0  # in days
        self.age_seconds = 0  # total seconds alive
        self.birth_date = None
        self.egg_start_time = datetime.now()
        self.last_update = datetime.now()
        self.state = DuckState.IDLE
        self.is_sleeping = False
        self.animation_frame = 0  # For sprite animation
        self.current_action = None  # Current interaction (eating, swimming, etc.)
        self.action_start_time = None
        
        # Personality system (initialized externally)
        self.personality_engine = None
        self.observer = None
        self.last_personality_update = datetime.now()
        
    def is_hatched(self):
        """Check if egg has hatched"""
        return self.stage == GameStage.DUCK
    
    def get_incubation_progress(self):
        """Get incubation progress as percentage (0-100)"""
        if self.is_hatched():
            return 100.0
        
        elapsed = (datetime.now() - self.egg_start_time).total_seconds()
        required = self.INCUBATION_HOURS * 3600  # Convert hours to seconds
        progress = min(100.0, (elapsed / required) * 100.0)
        return progress
    
    def can_hatch(self):
        """Check if egg can hatch (for testing button)"""
        return not self.is_hatched()
    
    def should_auto_hatch(self):
        """Check if egg should auto-hatch (5 hours passed)"""
        if self.is_hatched():
            return False
        elapsed = (datetime.now() - self.egg_start_time).total_seconds()
        required = self.INCUBATION_HOURS * 3600
        return elapsed >= required
    
    def hatch(self):
        """Hatch the egg"""
        if not self.is_hatched():
            self.stage = GameStage.DUCK
            self.birth_date = datetime.now()
            
            # Observe naming event if name is set
            if self.observer and self.name:
                self.observer.observe_naming_event(self.name, self.get_stats())
            
            return True
        return False
        
    def update(self):
        """Update duck stats based on time passed"""
        now = datetime.now()
        time_passed = (now - self.last_update).total_seconds()
        
        if self.is_hatched():
            # Update age
            self.age_seconds += time_passed
            self.age = self.age_seconds / 86400  # Convert to days
            
            # Handle current action
            if self.current_action:
                if self.action_start_time:
                    action_duration = (now - self.action_start_time).total_seconds()
                    if action_duration >= 3:  # Action completes after 3 seconds
                        self.complete_action()
                else:
                    self.action_start_time = now
            
            # Only decay if not sleeping and not in action
            if not self.is_sleeping and not self.current_action:
                # Decay rates (per second)
                self.hunger = max(self.MIN_STAT, self.hunger - time_passed * 0.01)
                self.happiness = max(self.MIN_STAT, self.happiness - time_passed * 0.005)
                self.energy = max(self.MIN_STAT, self.energy - time_passed * 0.008)
                self.cleanliness = max(self.MIN_STAT, self.cleanliness - time_passed * 0.003)
                
                # Health decreases if other stats are too low
                if self.hunger < 20 or self.happiness < 20 or self.cleanliness < 20:
                    self.health = max(self.MIN_STAT, self.health - time_passed * 0.005)
                elif self.health < self.MAX_STAT:
                    # Health regenerates slowly if other stats are good
                    self.health = min(self.MAX_STAT, self.health + time_passed * 0.002)
            elif self.is_sleeping:
                # Energy regenerates while sleeping
                self.energy = min(self.MAX_STAT, self.energy + time_passed * 0.15)
                if self.energy >= 90:
                    self.is_sleeping = False
                    self.state = DuckState.IDLE
            
            # Update animation frame
            self.animation_frame = (self.animation_frame + 1) % 2  # Toggle between 0 and 1
            
            old_state = self.state
            self._update_state()
            
            # Observe state changes
            if self.observer and old_state != self.state:
                self.observer.observe_duck_state_changed(
                    old_state=old_state.value,
                    new_state=self.state.value,
                    duck_stats=self.get_stats()
                )
            
            # Periodic personality update (every 5 minutes)
            if self.personality_engine:
                time_since_update = (now - self.last_personality_update).total_seconds()
                if time_since_update >= 300:  # 5 minutes
                    self.personality_engine.update_personality_periodically(
                        duck_stats=self.get_stats(),
                        min_new_memories=3
                    )
                    self.last_personality_update = now
        
        self.last_update = now
    
    def _update_state(self):
        """Update duck's current state based on stats"""
        if self.current_action:
            return  # Don't change state if in action
        
        if self.is_sleeping:
            self.state = DuckState.SLEEPING
        elif self.health < 30:
            self.state = DuckState.SICK
        elif self.hunger < 30:
            self.state = DuckState.HUNGRY
        elif self.energy < 30:
            self.state = DuckState.TIRED
        elif self.cleanliness < 30:
            self.state = DuckState.DIRTY
        elif self.happiness > 70 and self.hunger > 50:
            self.state = DuckState.HAPPY
        else:
            self.state = DuckState.IDLE
    
    def interact_with_item(self, item_type):
        """Interact with a placed item"""
        if not self.is_hatched() or self.is_sleeping:
            return False
        
        # Get stats before interaction
        stats_before = self.get_stats()
        
        if item_type == "pond":
            # Swimming
            self.current_action = "swimming"
            self.state = DuckState.SWIMMING
            self.happiness = min(self.MAX_STAT, self.happiness + 20)
            self.energy = max(self.MIN_STAT, self.energy - 10)
            self.cleanliness = min(self.MAX_STAT, self.cleanliness + 15)
            self.action_start_time = datetime.now()
            
            # Observe interaction
            if self.observer:
                self.observer.observe_item_interaction(item_type, self.get_stats())
            
            return True
        elif item_type == "grass":
            # Eating/Grazing
            self.current_action = "eating"
            self.state = DuckState.EATING
            self.hunger = min(self.MAX_STAT, self.hunger + 30)
            self.happiness = min(self.MAX_STAT, self.happiness + 10)
            self.action_start_time = datetime.now()
            
            # Observe interaction
            if self.observer:
                self.observer.observe_item_interaction(item_type, self.get_stats())
            
            return True
        elif item_type == "house":
            # Sleeping
            self.is_sleeping = True
            self.state = DuckState.SLEEPING
            self.current_action = "sleeping"
            self.action_start_time = datetime.now()
            
            # Observe interaction
            if self.observer:
                self.observer.observe_item_interaction(item_type, self.get_stats())
            
            return True
        
        return False
    
    def complete_action(self):
        """Complete current action"""
        self.current_action = None
        self.action_start_time = None
        self._update_state()
    
    def is_dead(self):
        """Check if duck has died (all stats at 0)"""
        return (self.is_hatched() and 
                self.hunger <= 0 and 
                self.happiness <= 0 and 
                self.health <= 0 and 
                self.energy <= 0 and 
                self.cleanliness <= 0)
    
    def get_stats(self):
        """Get current stats as a dictionary"""
        return {
            'stage': self.stage.value,
            'hunger': self.hunger,
            'happiness': self.happiness,
            'health': self.health,
            'energy': self.energy,
            'cleanliness': self.cleanliness,
            'age': self.age,
            'age_seconds': self.age_seconds,
            'state': self.state.value,
            'current_action': self.current_action,
            'is_sleeping': self.is_sleeping,
            'animation_frame': self.animation_frame
        }
    
    def save(self, filename="duck_save.json"):
        """Save duck state to file"""
        data = {
            'stage': self.stage.value,
            'name': self.name,
            'hunger': self.hunger,
            'happiness': self.happiness,
            'health': self.health,
            'energy': self.energy,
            'cleanliness': self.cleanliness,
            'age': self.age,
            'age_seconds': self.age_seconds,
            'egg_start_time': self.egg_start_time.isoformat(),
            'last_update': self.last_update.isoformat(),
            'is_sleeping': self.is_sleeping,
            'current_action': self.current_action,
            'action_start_time': self.action_start_time.isoformat() if self.action_start_time else None,
            'last_personality_update': self.last_personality_update.isoformat() if hasattr(self, 'last_personality_update') else None
        }
        if self.birth_date:
            data['birth_date'] = self.birth_date.isoformat()
        with open(filename, 'w') as f:
            json.dump(data, f)
    
    def load(self, filename="duck_save.json"):
        """Load duck state from file"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                self.stage = GameStage(data.get('stage', 'egg'))
                self.name = data.get('name', 'Ducky')
                self.hunger = data.get('hunger', 80)
                self.happiness = data.get('happiness', 80)
                self.health = data.get('health', 100)
                self.energy = data.get('energy', 80)
                self.cleanliness = data.get('cleanliness', 80)
                self.age = data.get('age', 0)
                self.age_seconds = data.get('age_seconds', 0)
                self.egg_start_time = datetime.fromisoformat(data.get('egg_start_time', datetime.now().isoformat()))
                self.last_update = datetime.fromisoformat(data.get('last_update', datetime.now().isoformat()))
                self.is_sleeping = data.get('is_sleeping', False)
                self.current_action = data.get('current_action', None)
                action_start = data.get('action_start_time')
                self.action_start_time = datetime.fromisoformat(action_start) if action_start else None
                birth_date = data.get('birth_date')
                self.birth_date = datetime.fromisoformat(birth_date) if birth_date else None
                last_personality_update = data.get('last_personality_update')
                if last_personality_update:
                    self.last_personality_update = datetime.fromisoformat(last_personality_update)
                else:
                    self.last_personality_update = datetime.now()
                self._update_state()
                return True
        return False
