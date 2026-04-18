"""
Observation System - Track user interactions and convert to memory entries
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from memory.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Observer:
    """
    Observes user interactions and logs them as memories in the vector store.
    """
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize observer.
        
        Args:
            vector_store: VectorStore instance for storing observations
        """
        self.vector_store = vector_store
        self.last_feed_time = None
        self.last_play_time = None
        self.feed_count = 0
        self.play_count = 0
        self.interaction_history = []
    
    def observe_user_fed_duck(
        self,
        duck_stats: Dict[str, Any],
        hunger_before: float,
        hunger_after: float
    ) -> str:
        """
        Observe when user feeds the duck.
        
        Args:
            duck_stats: Current duck stats
            hunger_before: Hunger level before feeding
            hunger_after: Hunger level after feeding
            
        Returns:
            Memory ID
        """
        now = datetime.now()
        time_since_last_feed = None
        if self.last_feed_time:
            time_since_last_feed = (now - self.last_feed_time).total_seconds() / 60  # minutes
        
        self.feed_count += 1
        self.last_feed_time = now
        
        # Build observation document
        doc_parts = [f"User fed the duck"]
        
        if hunger_before < 30:
            doc_parts.append("when duck was very hungry")
        elif hunger_before < 50:
            doc_parts.append("when duck was somewhat hungry")
        else:
            doc_parts.append("when duck was not particularly hungry")
        
        if time_since_last_feed:
            if time_since_last_feed < 5:
                doc_parts.append("(fed very recently)")
            elif time_since_last_feed < 30:
                doc_parts.append("(fed recently)")
        
        doc_parts.append(f"Hunger increased from {hunger_before:.1f} to {hunger_after:.1f}")
        
        document = ". ".join(doc_parts) + "."
        
        memory_id = self.vector_store.add_memory(
            document=document,
            event_type="user_fed_duck",
            stats_snapshot=duck_stats,
            user_action="fed_duck",
            metadata={
                "hunger_before": hunger_before,
                "hunger_after": hunger_after,
                "feed_count": self.feed_count,
                "time_since_last_feed_minutes": time_since_last_feed
            }
        )
        
        logger.info(f"Observed user feeding duck: {memory_id}")
        return memory_id
    
    def observe_item_interaction(
        self,
        item_type: str,
        duck_stats: Dict[str, Any]
    ) -> str:
        """
        Observe when duck interacts with an item.
        
        Args:
            item_type: Type of item (pond, grass, house)
            duck_stats: Current duck stats
            
        Returns:
            Memory ID
        """
        item_names = {
            "pond": "pond (swimming)",
            "grass": "grass (eating/grazing)",
            "house": "house (sleeping)"
        }
        
        item_name = item_names.get(item_type, item_type)
        
        document = f"Duck interacted with {item_name}. "
        
        if item_type == "pond":
            document += f"Happiness: {duck_stats.get('happiness', 0):.1f}, "
            document += f"Cleanliness: {duck_stats.get('cleanliness', 0):.1f}"
        elif item_type == "grass":
            document += f"Hunger: {duck_stats.get('hunger', 0):.1f}, "
            document += f"Happiness: {duck_stats.get('happiness', 0):.1f}"
        elif item_type == "house":
            document += f"Energy: {duck_stats.get('energy', 0):.1f}"
        
        memory_id = self.vector_store.add_memory(
            document=document,
            event_type="item_interaction",
            stats_snapshot=duck_stats,
            user_action=f"duck_interacted_with_{item_type}",
            metadata={"item_type": item_type}
        )
        
        logger.info(f"Observed item interaction: {memory_id}")
        return memory_id
    
    def observe_duck_state_changed(
        self,
        old_state: str,
        new_state: str,
        duck_stats: Dict[str, Any],
        user_action: Optional[str] = None
    ) -> Optional[str]:
        """
        Observe when duck's state changes.
        
        Args:
            old_state: Previous state
            new_state: New state
            duck_stats: Current duck stats
            user_action: User action that triggered change (if any)
            
        Returns:
            Memory ID or None if not significant
        """
        # Only log significant state changes
        significant_states = ["sick", "hungry", "tired", "happy"]
        if new_state not in significant_states:
            return None
        
        document = f"Duck state changed from {old_state} to {new_state}"
        
        if user_action:
            document += f" after user {user_action}"
        
        document += f". Current stats: Hunger={duck_stats.get('hunger', 0):.1f}, "
        document += f"Happiness={duck_stats.get('happiness', 0):.1f}, "
        document += f"Health={duck_stats.get('health', 0):.1f}"
        
        memory_id = self.vector_store.add_memory(
            document=document,
            event_type="duck_state_changed",
            stats_snapshot=duck_stats,
            user_action=user_action or "state_change",
            metadata={
                "old_state": old_state,
                "new_state": new_state
            }
        )
        
        logger.info(f"Observed state change: {memory_id}")
        return memory_id
    
    def observe_naming_event(
        self,
        name: str,
        duck_stats: Dict[str, Any]
    ) -> str:
        """
        Observe when duck is named.
        
        Args:
            name: Name given to duck
            duck_stats: Current duck stats
            
        Returns:
            Memory ID
        """
        document = f"User named the duck '{name}'. "
        
        # Analyze name for personality clues
        name_lower = name.lower()
        if any(word in name_lower for word in ["happy", "joy", "sunny", "bright"]):
            document += "Name suggests positive, cheerful personality."
        elif any(word in name_lower for word in ["cool", "chill", "calm", "zen"]):
            document += "Name suggests calm, relaxed personality."
        elif any(word in name_lower for word in ["adventure", "explore", "dash", "zoom"]):
            document += "Name suggests adventurous, active personality."
        
        memory_id = self.vector_store.add_memory(
            document=document,
            event_type="naming_event",
            stats_snapshot=duck_stats,
            user_action="named_duck",
            metadata={"name": name}
        )
        
        logger.info(f"Observed naming event: {memory_id}")
        return memory_id
    
    def observe_time_pattern(
        self,
        duck_stats: Dict[str, Any],
        active_hours: list
    ) -> str:
        """
        Observe time patterns of user activity.
        
        Args:
            duck_stats: Current duck stats
            active_hours: List of hours when user is most active
            
        Returns:
            Memory ID
        """
        if not active_hours:
            return None
        
        # Determine time of day pattern
        morning = [h for h in active_hours if 6 <= h < 12]
        afternoon = [h for h in active_hours if 12 <= h < 18]
        evening = [h for h in active_hours if 18 <= h < 24]
        night = [h for h in active_hours if 0 <= h < 6]
        
        patterns = []
        if morning:
            patterns.append("morning")
        if afternoon:
            patterns.append("afternoon")
        if evening:
            patterns.append("evening")
        if night:
            patterns.append("night")
        
        document = f"User is most active during {', '.join(patterns)}. "
        document += f"Active hours: {', '.join(map(str, active_hours[:5]))}"
        
        memory_id = self.vector_store.add_memory(
            document=document,
            event_type="time_pattern",
            stats_snapshot=duck_stats,
            user_action="time_analysis",
            metadata={
                "active_hours": active_hours,
                "patterns": patterns
            }
        )
        
        logger.info(f"Observed time pattern: {memory_id}")
        return memory_id
    
    def observe_chat_message(
        self,
        user_message: str,
        duck_stats: Dict[str, Any],
        is_on_topic: bool = True
    ) -> str:
        """
        Observe chat message from user.
        
        Args:
            user_message: User's chat message
            duck_stats: Current duck stats
            is_on_topic: Whether message was on-topic
            
        Returns:
            Memory ID
        """
        event_type = "chat_message" if is_on_topic else "chat_topic_violation"
        
        document = f"User said: '{user_message}'"
        if not is_on_topic:
            document += " (off-topic, redirected)"
        
        memory_id = self.vector_store.add_memory(
            document=document,
            event_type=event_type,
            stats_snapshot=duck_stats,
            user_action="chat",
            metadata={
                "message": user_message,
                "is_on_topic": is_on_topic
            }
        )
        
        logger.info(f"Observed chat message: {memory_id}")
        return memory_id
