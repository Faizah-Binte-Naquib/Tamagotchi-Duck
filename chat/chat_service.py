"""
Chat Service - Handle chat interactions with topic filtering and personality-aware responses
"""
import logging
import re
from typing import Dict, Any, Optional, Tuple
from llm.llm_service import LLMService
from llm.rag_service import RAGService
from chat.topic_filter import TopicFilter
from personality.personality_engine import PersonalityEngine
from prompts.chat_prompts import build_chat_prompt, get_chat_response_instructions

logger = logging.getLogger(__name__)


class ChatService:
    """
    Handles chat interactions with the duck.
    Includes topic filtering, personality-aware responses, and RAG context.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        rag_service: RAGService,
        personality_engine: PersonalityEngine,
        topic_filter: TopicFilter
    ):
        """
        Initialize chat service.
        
        Args:
            llm_service: LLMService instance
            rag_service: RAGService instance
            personality_engine: PersonalityEngine instance
            topic_filter: TopicFilter instance
        """
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.personality_engine = personality_engine
        self.topic_filter = topic_filter
    
    def process_message(
        self,
        user_message: str,
        duck_stats: Dict[str, Any],
        observer
    ) -> Tuple[str, bool]:
        """
        Process a user chat message.
        
        Args:
            user_message: User's message
            duck_stats: Current duck stats
            observer: Observer instance for logging
            
        Returns:
            Tuple of (response_message, is_on_topic)
        """
        # Check topic
        is_on_topic, confidence = self.topic_filter.classify_message(user_message)
        
        # Log message
        observer.observe_chat_message(
            user_message=user_message,
            duck_stats=duck_stats,
            is_on_topic=is_on_topic
        )
        
        if not is_on_topic:
            # Return redirect message
            redirect = self.topic_filter.get_redirect_message()
            return redirect, False
        
        # Generate response
        try:
            response = self._generate_response(
                user_message=user_message,
                duck_stats=duck_stats
            )
            
            # Post-process response
            response = self._post_process_response(response)
            
            return response, True
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            # Fallback response
            personality = self.personality_engine.get_personality()
            if personality.get("social", 0.5) > 0.7:
                return "That's interesting! *quacks happily*", True
            else:
                return "Hmm, I see. *nods*", True
    
    def _generate_response(
        self,
        user_message: str,
        duck_stats: Dict[str, Any]
    ) -> str:
        """
        Generate chat response using LLM.
        
        Args:
            user_message: User's message
            duck_stats: Current duck stats
            
        Returns:
            Generated response
        """
        # Get personality
        personality = self.personality_engine.get_personality()
        
        # Get relevant context
        context_memories = self.rag_service.build_context_for_chat(
            user_message=user_message,
            n_memories=5
        )
        
        # Build prompt
        prompt = build_chat_prompt(
            user_message=user_message,
            personality=personality,
            context_memories=context_memories,
            duck_stats=duck_stats
        )
        
        # Generate response
        response = self.llm_service.generate(
            prompt=prompt,
            max_tokens=100,  # Short responses
            temperature=0.8,  # More creative
            stop=["\n\n", "User:", "##"]
        )
        
        return response.strip()
    
    def _post_process_response(self, response: str) -> str:
        """
        Post-process response to ensure it meets requirements.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Processed response
        """
        # Remove markdown if present
        response = re.sub(r'```[a-z]*\n?', '', response)
        response = re.sub(r'```', '', response)
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Limit to 2 sentences
        if len(sentences) > 2:
            sentences = sentences[:2]
            response = '. '.join(sentences)
            if not response.endswith(('.', '!', '?')):
                response += '.'
        else:
            response = '. '.join(sentences)
            if not response.endswith(('.', '!', '?')):
                response += '.'
        
        # Remove questions that invite long replies
        question_patterns = [
            r'what do you think\?',
            r'tell me more',
            r'what else',
            r'can you explain',
            r'why do you',
        ]
        
        for pattern in question_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # Add natural ending if response is too short or doesn't have one
        if len(response) < 20:
            endings = ["*quacks*", "*waddles*", "*nods*"]
            import random
            response += " " + random.choice(endings)
        elif not any(marker in response for marker in ["*", "!", "."]):
            # Add a simple ending
            response += " *quacks*"
        
        # Clean up extra whitespace
        response = re.sub(r'\s+', ' ', response).strip()
        
        return response
