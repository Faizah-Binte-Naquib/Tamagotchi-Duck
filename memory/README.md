# Memory Vector Store Setup Guide

## Installation

The Chroma database is already included in `requirements.txt`. To set it up:

1. **Install dependencies** (if not already installed):
```bash
pip install -r requirements.txt
```

This will install:
- `chromadb>=0.4.0` - The vector database
- `sentence-transformers>=2.2.0` - For generating embeddings
- `numpy>=1.24.0` - Required dependency

2. **First-time setup**: The embedding model (`all-MiniLM-L6-v2`) will be automatically downloaded on first use (about 80MB).

## Usage

### Basic Setup

The `VectorStore` class handles all Chroma setup automatically. You can use it in two ways:

#### Option 1: Persistent Database (Recommended)
Stores data on disk, survives application restarts:

```python
from memory.vector_store import VectorStore

# Initialize with persistent storage
# Data will be saved in the "chroma_db" directory
vector_store = VectorStore(persist_directory="chroma_db")
```

#### Option 2: In-Memory Database
Data is lost when application closes (useful for testing):

```python
from memory.vector_store import VectorStore

# Initialize in-memory (no persistence)
vector_store = VectorStore()
```

### Adding Memories

```python
# Example: Log when user feeds the duck
memory_id = vector_store.add_memory(
    document="User fed the duck when hunger was at 30%. Duck was happy.",duck
    event_type="user_fed_duck",
    stats_snapshot={
        "hunger": 30,
        "happiness": 75,duck
        "health": 90,
        "energy": 60
    },duck
    user_action="fed_duck"
)
```

### Searching Memoriesduck
duck
```python
# Search for similar memories
results = vector_store.search_similar(
    query="user feeding patterns when duck is hungry",
    n_results=5
)

for result in results:
    print(f"Memory: {result['document']}")
    print(f"Event: {result['metadata']['event_type']}")
    print(f"Similarity: {result['distance']}")
    print("---")
```

### Filtering by Event Type

```python
# Get all feeding events
feeding_memories = vector_store.get_memories_by_event_type(
    event_type="user_fed_duck",
    limit=10
)
```

### Getting Recent Memories

```python
# Get 10 most recent memories
recent = vector_store.get_recent_memories(limit=10)
```

## Database Location

When using persistent storage:
- Default location: `chroma_db/` directory in your project root
- You can specify any path: `VectorStore(persist_directory="./data/memories")`
- The directory will be created automatically if it doesn't exist

## Event Types

Common event types you can use (from the plan):
- `user_fed_duck` - When user feeds the duck
- `user_played_with_duck` - When user plays with duck
- `duck_state_changed` - When duck's state changes
- `item_interaction` - When duck interacts with items (pond, grass, house)
- `naming_event` - When duck is named
- `time_pattern` - Time-based patterns
- `chat_message` - User chat messages (on-topic)
- `chat_topic_violation` - Off-topic messages

## Notes

- The embedding model downloads automatically on first use (~80MB)
- Chroma creates the collection automatically on first use
- All metadata is stored as strings/numbers (complex objects are JSON-encoded)
- The database is thread-safe and can be used across multiple parts of your application
