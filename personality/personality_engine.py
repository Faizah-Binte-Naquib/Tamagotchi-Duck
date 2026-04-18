"""
Personality Engine - Core personality system using LLM+RAG
"""
import json
import os
import logging
from typing import Dict, Any, Optional
from llm.llm_service import LLMService
from llm.rag_service import RAGService
from prompts.personality_prompts import build_personality_prompt, get_personality_update_prompt
from prompts.few_shot_examples import get_few_shot_examples

logger = logging.getLogger(__name__)


class PersonalityEngine:
    """
    Generates and updates duck personality based on observations using LLM and RAG.
    """
    
    DEFAULT_PERSONALITY = {
        "playfulness": 0.5,
        "independence": 0.5,
        "social": 0.5,
        "preferences": {
            "favorite_activity": "eating",
            "preferred_time": "afternoon",
            "dislikes": []
        },
        "quirks": [],
        "personality_description": "A friendly duck with a balanced personality."
    }
    
    def __init__(
        self,
        llm_service: LLMService,
        rag_service: RAGService,
        personality_file: str = "duck_personality.json"
    ):
        """
        Initialize personality engine.
        
        Args:
            llm_service: LLMService instance
            rag_service: RAGService instance
            personality_file: Path to store personality JSON
        """
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.personality_file = personality_file
        self.personality = self._load_personality()
        self.few_shot_examples = get_few_shot_examples()
    
    def _load_personality(self) -> Dict[str, Any]:
        """Load personality from file or return default"""
        if os.path.exists(self.personality_file):
            try:
                with open(self.personality_file, 'r') as f:
                    personality = json.load(f)
                    logger.info("Loaded existing personality")
                    return personality
            except Exception as e:
                logger.warning(f"Failed to load personality: {e}")
        
        return self.DEFAULT_PERSONALITY.copy()
    
    def _save_personality(self) -> None:
        """Save personality to file"""
        try:
            with open(self.personality_file, 'w') as f:
                json.dump(self.personality, f, indent=2)
            logger.info("Saved personality to file")
        except Exception as e:
            logger.error(f"Failed to save personality: {e}")
    
    def generate_personality(
        self,
        duck_stats: Dict[str, Any],
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate or update personality based on observations.
        
        Args:
            duck_stats: Current duck stats
            force_regenerate: Force regeneration even if personality exists
            
        Returns:
            Updated personality dictionary
        """
        # Check if we have enough observations
        memory_count = self.rag_service.vector_store.get_memory_count()
        
        if memory_count < 3 and not force_regenerate:
            logger.info("Not enough observations yet, using default personality")
            return self.personality
        
        # Get relevant memories
        memories = self.rag_service.build_context_for_personality(
            current_stats=duck_stats,
            n_memories=15
        )
        
        if not memories and not force_regenerate:
            logger.info("No relevant memories found, using default personality")
            return self.personality
        
        try:
            # Build prompt
            if force_regenerate or not self.personality.get("personality_description"):
                # Initial generation
                prompt = build_personality_prompt(
                    observations=memories,
                    few_shot_examples=self.few_shot_examples,
                    current_stats=duck_stats
                )
            else:
                # Update existing personality
                prompt = get_personality_update_prompt(
                    current_personality=self.personality,
                    new_observations=memories[-5:]  # Last 5 observations
                )
            
            # Generate personality using LLM
            logger.info("Generating personality with LLM...")
            new_personality = self.llm_service.generate_json(
                prompt=prompt,
                max_tokens=512,
                temperature=0.7
            )
            
            # Validate and merge personality
            self.personality = self._merge_personality(new_personality)
            self._save_personality()
            
            logger.info("Personality generated successfully")
            return self.personality
            
        except Exception as e:
            logger.error(f"Failed to generate personality: {e}")
            return self.personality
    
    def _merge_personality(self, new_personality: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge new personality with existing, ensuring all required fields.
        
        Args:
            new_personality: New personality from LLM
            
        Returns:
            Merged personality dictionary
        """
        merged = self.personality.copy()
        
        # Update numeric traits (weighted average for smooth transitions)
        for trait in ["playfulness", "independence", "social"]:
            if trait in new_personality:
                new_value = float(new_personality[trait])
                old_value = merged.get(trait, 0.5)
                # Weighted average: 70% new, 30% old (smooth transition)
                merged[trait] = 0.7 * new_value + 0.3 * old_value
                # Clamp to [0, 1]
                merged[trait] = max(0.0, min(1.0, merged[trait]))
        
        # Update preferences
        if "preferences" in new_personality:
            merged["preferences"] = {
                **merged.get("preferences", {}),
                **new_personality["preferences"]
            }
        
        # Update quirks (append new ones, keep old ones)
        if "quirks" in new_personality:
            existing_quirks = set(merged.get("quirks", []))
            new_quirks = new_personality["quirks"]
            for quirk in new_quirks:
                if quirk not in existing_quirks:
                    merged.setdefault("quirks", []).append(quirk)
            # Limit to 5 quirks
            merged["quirks"] = merged.get("quirks", [])[:5]
        
        # Update description
        if "personality_description" in new_personality:
            merged["personality_description"] = new_personality["personality_description"]
        
        return merged
    
    def get_personality(self) -> Dict[str, Any]:
        """Get current personality"""
        return self.personality.copy()
    
    def update_personality_periodically(
        self,
        duck_stats: Dict[str, Any],
        min_new_memories: int = 5
    ) -> bool:
        """
        Update personality if enough new memories have been added.
        
        Args:
            duck_stats: Current duck stats
            min_new_memories: Minimum new memories needed to trigger update
            
        Returns:
            True if personality was updated
        """
        memory_count = self.rag_service.vector_store.get_memory_count()
        
        # Check if we should update (every N new memories)
        if memory_count % min_new_memories == 0 and memory_count > 0:
            logger.info(f"Updating personality (memory count: {memory_count})")
            self.generate_personality(duck_stats, force_regenerate=False)
            return True
        
        return False
    
    def get_personality_trait(self, trait_name: str) -> float:
        """
        Get a specific personality trait value.
        
        Args:
            trait_name: Name of trait (playfulness, independence, social)
            
        Returns:
            Trait value (0.0-1.0)
        """
        return self.personality.get(trait_name, 0.5)
    
    def get_preference(self, preference_name: str) -> Any:
        """
        Get a preference value.
        
        Args:
            preference_name: Name of preference
            
        Returns:
            Preference value or None
        """
        preferences = self.personality.get("preferences", {})
        return preferences.get(preference_name)
