"""
Few-shot learning examples for personality generation
These examples guide the LLM in generating personality profiles
"""
from typing import List, Dict, Any


def get_few_shot_examples() -> List[Dict[str, Any]]:
    """
    Get few-shot examples for personality generation.
    
    Returns:
        List of example observations and their corresponding personalities
    """
    return [
        {
            "observations": [
                "User frequently feeds duck when hunger is low",
                "Duck often interacts with pond, loves swimming",
                "User plays with duck multiple times per day",
                "Duck shows high happiness when user is active"
            ],
            "personality": {
                "playfulness": 0.8,
                "independence": 0.6,
                "social": 0.9,
                "preferences": {
                    "favorite_activity": "swimming",
                    "preferred_time": "afternoon",
                    "dislikes": ["being ignored", "low energy"]
                },
                "quirks": [
                    "loves to quack when happy",
                    "prefers pond over other activities",
                    "seeks attention from user"
                ],
                "personality_description": "A playful and social duck who loves swimming and interacting with the user. Very active and seeks attention, especially in the afternoon."
            }
        },
        {
            "observations": [
                "User feeds duck regularly but not frequently",
                "Duck prefers grass/feeding over other activities",
                "Duck often sleeps and rests",
                "User interacts less frequently, duck seems content alone"
            ],
            "personality": {
                "playfulness": 0.4,
                "independence": 0.8,
                "social": 0.5,
                "preferences": {
                    "favorite_activity": "eating",
                    "preferred_time": "evening",
                    "dislikes": ["too much activity", "being disturbed while resting"]
                },
                "quirks": [
                    "enjoys quiet moments",
                    "prefers grazing over swimming",
                    "content with minimal interaction"
                ],
                "personality_description": "A calm and independent duck who enjoys quiet activities like eating and resting. Prefers less frequent interactions and values personal space."
            }
        },
        {
            "observations": [
                "User plays with duck very frequently",
                "Duck interacts with all items equally",
                "Duck shows high energy and activity",
                "User responds quickly to duck's needs"
            ],
            "personality": {
                "playfulness": 0.9,
                "independence": 0.3,
                "social": 0.95,
                "preferences": {
                    "favorite_activity": "playing",
                    "preferred_time": "morning",
                    "dislikes": ["boredom", "being alone"]
                },
                "quirks": [
                    "very energetic in the morning",
                    "loves all activities equally",
                    "always wants to interact"
                ],
                "personality_description": "An extremely playful and social duck who loves all activities and craves constant interaction. Very energetic, especially in the morning, and dislikes being alone."
            }
        },
        {
            "observations": [
                "User feeds duck when hungry but not proactively",
                "Duck explores and walks around frequently",
                "Duck shows moderate interaction with items",
                "User interacts occasionally, duck seems self-sufficient"
            ],
            "personality": {
                "playfulness": 0.6,
                "independence": 0.9,
                "social": 0.4,
                "preferences": {
                    "favorite_activity": "walking",
                    "preferred_time": "afternoon",
                    "dislikes": ["being confined", "too much attention"]
                },
                "quirks": [
                    "loves exploring",
                    "enjoys walking around",
                    "prefers moderate interaction"
                ],
                "personality_description": "An adventurous and independent duck who loves exploring and walking around. Self-sufficient and prefers moderate interaction, enjoying the freedom to explore."
            }
        }
    ]


def get_personality_dimensions() -> Dict[str, str]:
    """
    Get descriptions of personality dimensions.
    
    Returns:
        Dictionary mapping dimension names to descriptions
    """
    return {
        "playfulness": "How much the duck enjoys playing and active activities (0.0 = prefers rest, 1.0 = very playful)",
        "independence": "How self-sufficient the duck is (0.0 = needs constant attention, 1.0 = very independent)",
        "social": "How much the duck seeks interaction (0.0 = prefers solitude, 1.0 = very social)"
    }
