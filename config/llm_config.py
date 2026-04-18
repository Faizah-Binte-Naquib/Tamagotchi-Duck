"""
LLM Configuration - Ollama only
Configuration for Ollama LLM service
"""
import os
from pathlib import Path


class LLMConfig:
    """Configuration for LLM service (Ollama only)"""
    
    # Ollama configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama3.1:8b"
    
    # LLM settings
    MAX_TOKENS = 512
    TEMPERATURE = 0.7
    TOP_P = 0.9
    
    # Context window
    CONTEXT_WINDOW = 4096
    
    # Embedding model (for vector store)
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # Vector DB path
    VECTOR_DB_PATH = os.path.join(
        Path(__file__).parent.parent,
        "chroma_db"
    )
    
    @classmethod
    def get_vector_db_path(cls) -> str:
        """Get the path for vector database storage"""
        return cls.VECTOR_DB_PATH
    
    @classmethod
    def ensure_vector_db_directory(cls) -> None:
        """Ensure the vector DB directory exists"""
        os.makedirs(cls.VECTOR_DB_PATH, exist_ok=True)
