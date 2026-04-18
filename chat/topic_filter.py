"""
Topic Filter - Classify messages as duck-related or off-topic
"""
import logging
from typing import Dict, Any, Tuple
from llm.llm_service import LLMService

logger = logging.getLogger(__name__)


class TopicFilter:
    """
    Filters chat messages to ensure they're duck-related.
    Uses LLM to classify message relevance.
    """
    
    TOPIC_CLASSIFICATION_PROMPT = """Classify whether the following user message is about the duck, their relationship with the duck, or duck-related topics.

ON-TOPIC (duck_related):
- Duck's personality, feelings, preferences
- Care activities (feeding, playing, etc.)
- User's feelings about the duck
- Duck's activities and behaviors
- Bonding moments and memories
- Questions about how the duck is doing
- Compliments or concerns about the duck

OFF-TOPIC:
- General knowledge questions
- Unrelated personal topics
- Requests for information about other subjects
- Long philosophical discussions
- Questions about the user's own life (unless related to duck)
- Technical questions about the app

User message: "{message}"

Respond with ONLY one word: "duck_related" or "off_topic" followed by a confidence score 0.0-1.0.

Format: duck_related 0.85
or: off_topic 0.90"""

    def __init__(self, llm_service: LLMService, confidence_threshold: float = 0.7):
        """
        Initialize topic filter.
        
        Args:
            llm_service: LLMService instance
            confidence_threshold: Minimum confidence for duck-related classification
        """
        self.llm_service = llm_service
        self.confidence_threshold = confidence_threshold
    
    def classify_message(self, message: str) -> Tuple[bool, float]:
        """
        Classify if a message is duck-related.
        
        Args:
            message: User's message
            
        Returns:
            Tuple of (is_on_topic: bool, confidence: float)
        """
        if not message or len(message.strip()) == 0:
            return False, 0.0
        
        # Simple keyword-based pre-filter for obvious cases
        duck_keywords = [
            "duck", "you", "your", "quack", "feed", "play", "happy", "sad",
            "hungry", "tired", "swim", "pond", "grass", "house", "care",
            "love", "like", "friend", "pet", "companion"
        ]
        
        message_lower = message.lower()
        has_duck_keywords = any(keyword in message_lower for keyword in duck_keywords)
        
        # If no duck keywords and message is long, likely off-topic
        if not has_duck_keywords and len(message) > 50:
            return False, 0.3
        
        # Use LLM for classification
        try:
            prompt = self.TOPIC_CLASSIFICATION_PROMPT.format(message=message)
            response = self.llm_service.generate(
                prompt=prompt,
                max_tokens=20,
                temperature=0.3  # Lower temperature for classification
            )
            
            # Parse response
            response = response.strip().lower()
            
            is_on_topic = "duck_related" in response
            confidence = 0.5  # Default
            
            # Try to extract confidence score
            try:
                import re
                match = re.search(r'(\d+\.?\d*)', response)
                if match:
                    confidence = float(match.group(1))
                    if confidence > 1.0:
                        confidence = confidence / 100.0  # Convert percentage
            except:
                pass
            
            # Adjust confidence based on keyword presence
            if has_duck_keywords and is_on_topic:
                confidence = min(1.0, confidence + 0.1)
            elif not has_duck_keywords and is_on_topic:
                confidence = max(0.0, confidence - 0.2)
            
            is_valid = is_on_topic and confidence >= self.confidence_threshold
            
            logger.info(f"Topic classification: {is_valid} (confidence: {confidence:.2f})")
            return is_valid, confidence
            
        except Exception as e:
            logger.error(f"Error classifying message: {e}")
            # Fallback to keyword-based classification
            return has_duck_keywords, 0.6 if has_duck_keywords else 0.3
    
    def get_redirect_message(self) -> str:
        """
        Get a friendly redirect message for off-topic messages.
        
        Returns:
            Redirect message string
        """
        redirects = [
            "I'd love to chat about us! What's on your mind about me?",
            "Let's talk about you and me! How are you feeling about our time together?",
            "I'm here to chat about us! What would you like to share about our friendship?",
            "Tell me about how you're feeling about me! I'd love to hear your thoughts."
        ]
        
        import random
        return random.choice(redirects)
