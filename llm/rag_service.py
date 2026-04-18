"""
RAG (Retrieval-Augmented Generation) Service
Retrieves relevant memories from vector DB for LLM context
"""
import logging
from typing import List, Dict, Any, Optional
from memory.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG service for retrieving relevant memories and building context.
    """
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize RAG service.
        
        Args:
            vector_store: VectorStore instance for memory retrieval
        """
        self.vector_store = vector_store
    
    def retrieve_relevant_memories(
        self,
        query: str,
        n_results: int = 5,
        event_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories using semantic search.
        
        Args:
            query: Query text to search for similar memories
            n_results: Number of results to return
            event_type_filter: Optional event type to filter by
            
        Returns:
            List of relevant memory dictionaries
        """
        filter_metadata = None
        if event_type_filter:
            filter_metadata = {"event_type": event_type_filter}
        
        results = self.vector_store.search_similar(
            query=query,
            n_results=n_results,
            filter_metadata=filter_metadata
        )
        
        return results
    
    def build_context_for_personality(
        self,
        current_stats: Dict[str, Any],
        n_memories: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Build context for personality generation.
        
        Args:
            current_stats: Current duck stats
            n_memories: Number of memories to retrieve
            
        Returns:
            List of relevant memories
        """
        # Build query based on current context
        query_parts = []
        
        if current_stats.get('hunger', 50) < 30:
            query_parts.append("user feeding patterns when duck is hungry")
        if current_stats.get('happiness', 50) > 70:
            query_parts.append("user interactions when duck is happy")
        if current_stats.get('energy', 50) < 30:
            query_parts.append("duck resting and energy patterns")
        
        query = " ".join(query_parts) if query_parts else "user interaction patterns with duck"
        
        # Retrieve relevant memories
        memories = self.retrieve_relevant_memories(
            query=query,
            n_results=n_memories
        )
        
        # Also get recent memories to ensure we have latest context
        recent = self.vector_store.get_recent_memories(limit=5)
        
        # Combine and deduplicate by ID
        all_memories = {}
        for mem in memories + recent:
            mem_id = mem.get('id')
            if mem_id and mem_id not in all_memories:
                all_memories[mem_id] = mem
        
        return list(all_memories.values())[:n_memories]
    
    def build_context_for_chat(
        self,
        user_message: str,
        n_memories: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Build context for chat response generation.
        
        Args:
            user_message: User's chat message
            n_memories: Number of memories to retrieve
            
        Returns:
            List of relevant memories
        """
        # Search for memories related to the chat message
        memories = self.retrieve_relevant_memories(
            query=user_message,
            n_results=n_memories
        )
        
        # Also get recent chat messages if any
        chat_memories = self.retrieve_relevant_memories(
            query=user_message,
            n_results=3,
            event_type_filter="chat_message"
        )
        
        # Combine and deduplicate
        all_memories = {}
        for mem in memories + chat_memories:
            mem_id = mem.get('id')
            if mem_id and mem_id not in all_memories:
                all_memories[mem_id] = mem
        
        return list(all_memories.values())[:n_memories]
    
    def summarize_memories(
        self,
        memories: List[Dict[str, Any]],
        max_length: int = 500
    ) -> str:
        """
        Create a text summary of memories for LLM context.
        
        Args:
            memories: List of memory dictionaries
            max_length: Maximum length of summary
            
        Returns:
            Text summary
        """
        if not memories:
            return "No relevant memories found."
        
        summary_parts = []
        current_length = 0
        
        for mem in memories:
            doc = mem.get('document', '')
            event_type = mem.get('metadata', {}).get('event_type', 'unknown')
            
            line = f"[{event_type}] {doc}"
            if current_length + len(line) > max_length:
                break
            
            summary_parts.append(line)
            current_length += len(line) + 1
        
        return "\n".join(summary_parts)
    
    def get_interaction_patterns(
        self,
        event_type: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze interaction patterns for a specific event type.
        
        Args:
            event_type: Type of event to analyze
            limit: Maximum number of events to analyze
            
        Returns:
            Dictionary with pattern analysis
        """
        memories = self.vector_store.get_memories_by_event_type(
            event_type=event_type,
            limit=limit
        )
        
        if not memories:
            return {
                "count": 0,
                "frequency": "none",
                "pattern": "no_data"
            }
        
        # Analyze frequency
        count = len(memories)
        if count >= 15:
            frequency = "very_frequent"
        elif count >= 10:
            frequency = "frequent"
        elif count >= 5:
            frequency = "moderate"
        else:
            frequency = "occasional"
        
        # Analyze timing patterns (if timestamps available)
        # This is a simple analysis - could be enhanced
        return {
            "count": count,
            "frequency": frequency,
            "pattern": "consistent" if count >= 10 else "sporadic",
            "recent_count": len([m for m in memories[:5] if m])  # Last 5
        }
