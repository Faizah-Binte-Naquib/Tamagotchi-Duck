"""
Chroma vector store wrapper for storing and retrieving duck memories.

This module provides a vector database interface for storing observations
and memories about the duck's interactions, which will be used for
personality development via RAG (Retrieval-Augmented Generation).
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class VectorStore:
    """
    Chroma wrapper for storing and retrieving duck memories.
    
    Stores memories as embeddings with metadata for RAG retrieval.
    Uses sentence-transformers for generating embeddings.
    """
    
    COLLECTION_NAME = "duck_memories"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Directory to persist Chroma database.
                              If None, uses in-memory database.
        """
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.EMBEDDING_MODEL)
        
        # Initialize Chroma client
        if persist_directory:
            # Persistent database
            os.makedirs(persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            # In-memory database
            self.client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False)
            )
        
        # Get or create collection
        # We'll use a custom embedding function that uses our sentence-transformer model
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "DuckMind memories and observations"}
        )
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def add_memory(
        self,
        document: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        stats_snapshot: Optional[Dict[str, Any]] = None,
        user_action: Optional[str] = None
    ) -> str:
        """
        Add a memory to the vector store.
        
        Args:
            document: Text description of the memory/observation (will be embedded)
            event_type: Type of event (e.g., "user_fed_duck", "user_played_with_duck")
            metadata: Additional metadata dictionary
            stats_snapshot: Snapshot of duck stats at time of event
            user_action: Description of user action that triggered this memory
            
        Returns:
            ID of the added memory
        """
        # Generate embedding
        embedding = self._generate_embedding(document)
        
        # Prepare metadata
        memory_metadata = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
        }
        
        if stats_snapshot:
            # Store stats as JSON string (Chroma metadata must be strings/numbers)
            memory_metadata["stats_snapshot"] = json.dumps(stats_snapshot)
        
        if user_action:
            memory_metadata["user_action"] = user_action
        
        # Add any additional metadata
        if metadata:
            for key, value in metadata.items():
                # Convert non-string values to JSON strings
                if isinstance(value, (dict, list)):
                    memory_metadata[key] = json.dumps(value)
                elif isinstance(value, (str, int, float, bool)):
                    memory_metadata[key] = value
                else:
                    memory_metadata[key] = str(value)
        
        # Generate unique ID
        memory_id = f"{event_type}_{datetime.now().timestamp()}"
        
        # Add to collection
        # Note: Chroma can use provided embeddings or generate its own
        # We'll provide our own embeddings for consistency
        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[memory_metadata]
        )
        
        return memory_id
    
    def search_similar(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar memories using semantic similarity.
        
        Args:
            query: Query text to search for
            n_results: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"event_type": "user_fed_duck"})
            
        Returns:
            List of dictionaries containing:
            - id: Memory ID
            - document: Original document text
            - metadata: Memory metadata
            - distance: Similarity distance (lower is more similar)
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Prepare where clause for filtering
        where = None
        if filter_metadata:
            where = filter_metadata
        
        # Search collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                result = {
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                }
                
                # Parse JSON strings in metadata back to objects
                if 'stats_snapshot' in result['metadata']:
                    try:
                        result['metadata']['stats_snapshot'] = json.loads(
                            result['metadata']['stats_snapshot']
                        )
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                formatted_results.append(result)
        
        return formatted_results
    
    def get_memories_by_event_type(
        self,
        event_type: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all memories of a specific event type.
        
        Args:
            event_type: Type of event to filter by
            limit: Maximum number of results (None for all)
            
        Returns:
            List of memory dictionaries
        """
        # Use search with filter and a generic query
        results = self.search_similar(
            query="memory",
            n_results=limit or 1000,  # Large number to get all
            filter_metadata={"event_type": event_type}
        )
        
        return results
    
    def get_recent_memories(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get the most recent memories.
        
        Args:
            limit: Number of recent memories to return
            
        Returns:
            List of memory dictionaries, sorted by timestamp (newest first)
        """
        # Get all memories (we'll need to fetch and sort by timestamp)
        # Chroma doesn't have built-in timestamp sorting, so we'll get all and sort
        all_results = self.collection.get()
        
        if not all_results['ids']:
            return []
        
        # Combine data
        memories = []
        for i in range(len(all_results['ids'])):
            memory = {
                'id': all_results['ids'][i],
                'document': all_results['documents'][i],
                'metadata': all_results['metadatas'][i]
            }
            
            # Parse stats_snapshot if present
            if 'stats_snapshot' in memory['metadata']:
                try:
                    memory['metadata']['stats_snapshot'] = json.loads(
                        memory['metadata']['stats_snapshot']
                    )
                except (json.JSONDecodeError, TypeError):
                    pass
            
            memories.append(memory)
        
        # Sort by timestamp (newest first)
        memories.sort(
            key=lambda x: x['metadata'].get('timestamp', ''),
            reverse=True
        )
        
        return memories[:limit]
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False
    
    def clear_all_memories(self) -> None:
        """
        Clear all memories from the collection.
        """
        # Delete collection and recreate
        self.client.delete_collection(name=self.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "DuckMind memories and observations"}
        )
    
    def get_memory_count(self) -> int:
        """
        Get the total number of memories stored.
        
        Returns:
            Number of memories
        """
        count = self.collection.count()
        return count
    
    def get_stats_snapshot(self, memory: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and parse stats snapshot from a memory.
        
        Args:
            memory: Memory dictionary
            
        Returns:
            Parsed stats snapshot or None
        """
        metadata = memory.get('metadata', {})
        stats_json = metadata.get('stats_snapshot')
        
        if stats_json:
            try:
                if isinstance(stats_json, str):
                    return json.loads(stats_json)
                return stats_json
            except (json.JSONDecodeError, TypeError):
                return None
        
        return None
