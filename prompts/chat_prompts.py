"""
Chat response prompts for duck conversations
"""
from typing import Dict, Any, List


def get_chat_system_prompt(personality: Dict[str, Any]) -> str:
    """
    Get system prompt for chat responses based on personality.
    
    Args:
        personality: Current personality profile
        
    Returns:
        System prompt string
    """
    personality_desc = personality.get("personality_description", "A friendly duck")
    playfulness = personality.get("playfulness", 0.5)
    social = personality.get("social", 0.5)
    
    prompt = f"""You are a virtual duck with the following personality: {personality_desc}

Personality traits:
- Playfulness: {playfulness:.1f}/1.0
- Social: {social:.1f}/1.0

IMPORTANT RULES:
1. Keep responses to 1-2 SHORT sentences maximum
2. Be friendly and duck-like
3. Reflect your personality traits in your responses
4. Use simple language
5. Don't ask follow-up questions that invite long conversations
6. End responses naturally (e.g., "*waddles away*", "*quacks happily*")
7. Be concise and warm

Your quirks: {', '.join(personality.get('quirks', []))}

Respond as this duck would, based on your personality."""
    
    return prompt


def build_chat_prompt(
    user_message: str,
    personality: Dict[str, Any],
    context_memories: List[Dict[str, Any]],
    duck_stats: Dict[str, Any]
) -> str:
    """
    Build prompt for chat response generation.
    
    Args:
        user_message: User's message
        personality: Current personality profile
        context_memories: Relevant memories from RAG
        duck_stats: Current duck stats
        
    Returns:
        Formatted prompt string
    """
    prompt = get_chat_system_prompt(personality)
    
    # Add context from memories
    if context_memories:
        prompt += "\n\n## Relevant Past Conversations:\n"
        for mem in context_memories[:3]:  # Last 3 relevant memories
            doc = mem.get('document', '')
            if 'chat' in mem.get('metadata', {}).get('event_type', ''):
                prompt += f"- {doc}\n"
    
    # Add current state
    prompt += f"\n## Your Current State:\n"
    prompt += f"Happiness: {duck_stats.get('happiness', 0):.1f}/100\n"
    prompt += f"Hunger: {duck_stats.get('hunger', 0):.1f}/100\n"
    prompt += f"Energy: {duck_stats.get('energy', 0):.1f}/100\n"
    
    state = duck_stats.get('state', 'idle')
    prompt += f"State: {state}\n"
    
    # Add user message
    prompt += f"\n## User Message:\n{user_message}\n\n"
    prompt += "## Your Response:\n"
    prompt += "Respond in 1-2 short sentences, reflecting your personality. End naturally."
    
    return prompt


def get_chat_response_instructions() -> str:
    """Get instructions for post-processing chat responses"""
    return """
Post-processing rules:
1. Maximum 2 sentences
2. Remove any questions that invite long replies
3. Add natural endings like "*waddles away*" or "*quacks*"
4. Keep it warm and friendly
5. Reflect the duck's personality traits
"""
