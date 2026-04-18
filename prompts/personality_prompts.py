"""
Prompt templates for personality generation
"""
from typing import List, Dict, Any


def get_personality_system_prompt() -> str:
    """Get the system prompt for personality generation"""
    return """You are analyzing a virtual duck's personality based on observations of user interactions.

Your task is to generate personality traits and characteristics that reflect how the duck behaves and responds based on:
1. User interaction patterns (feeding, playing, care)
2. Duck's preferences and behaviors
3. Time patterns and activity levels
4. User's relationship with the duck

Generate personality traits in JSON format with the following structure:
{
    "playfulness": 0.0-1.0,
    "independence": 0.0-1.0,
    "social": 0.0-1.0,
    "preferences": {
        "favorite_activity": "swimming|eating|playing|sleeping",
        "preferred_time": "morning|afternoon|evening|night",
        "dislikes": ["list", "of", "dislikes"]
    },
    "quirks": ["unique behavior 1", "unique behavior 2"],
    "personality_description": "A brief 2-3 sentence description of the duck's personality"
}

Be creative but consistent with the observations. The personality should evolve naturally over time."""


def build_personality_prompt(
    observations: List[Dict[str, Any]],
    few_shot_examples: List[Dict[str, Any]],
    current_stats: Dict[str, Any]
) -> str:
    """
    Build a prompt for personality generation.
    
    Args:
        observations: List of recent observations/memories
        few_shot_examples: Example personality profiles for few-shot learning
        current_stats: Current duck stats
        
    Returns:
        Formatted prompt string
    """
    prompt = get_personality_system_prompt()
    prompt += "\n\n## Few-Shot Examples:\n\n"
    
    for i, example in enumerate(few_shot_examples, 1):
        prompt += f"Example {i}:\n"
        prompt += f"Observations: {example.get('observations', 'N/A')}\n"
        prompt += f"Personality: {example.get('personality', {})}\n\n"
    
    prompt += "## Current Observations:\n\n"
    for obs in observations[-10:]:  # Last 10 observations
        prompt += f"- {obs.get('document', 'N/A')}\n"
        if 'metadata' in obs and 'event_type' in obs['metadata']:
            prompt += f"  Event: {obs['metadata']['event_type']}\n"
    
    prompt += f"\n## Current Duck Stats:\n"
    prompt += f"Hunger: {current_stats.get('hunger', 0):.1f}\n"
    prompt += f"Happiness: {current_stats.get('happiness', 0):.1f}\n"
    prompt += f"Health: {current_stats.get('health', 0):.1f}\n"
    prompt += f"Energy: {current_stats.get('energy', 0):.1f}\n"
    prompt += f"Cleanliness: {current_stats.get('cleanliness', 0):.1f}\n"
    prompt += f"Age: {current_stats.get('age', 0):.2f} days\n"
    
    prompt += "\n## Task:\n"
    prompt += "Based on the observations and examples above, generate an updated personality profile in JSON format."
    prompt += " Consider how the duck's personality has developed based on user interactions."
    
    return prompt


def get_personality_update_prompt(
    current_personality: Dict[str, Any],
    new_observations: List[Dict[str, Any]]
) -> str:
    """
    Build a prompt for updating existing personality.
    
    Args:
        current_personality: Current personality profile
        new_observations: New observations since last update
        
    Returns:
        Formatted prompt string
    """
    prompt = get_personality_system_prompt()
    prompt += "\n\n## Current Personality:\n"
    prompt += f"{current_personality}\n\n"
    
    prompt += "## New Observations:\n"
    for obs in new_observations:
        prompt += f"- {obs.get('document', 'N/A')}\n"
    
    prompt += "\n## Task:\n"
    prompt += "Update the personality profile based on new observations."
    prompt += " Make incremental changes that reflect the duck's evolving personality."
    prompt += " Return the updated personality in JSON format."
    
    return prompt
