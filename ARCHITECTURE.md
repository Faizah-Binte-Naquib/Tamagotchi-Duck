# Architecture Documentation

## System Overview

The DuckMind project is built with a modular architecture that separates game logic from AI/ML systems. The ML components use a RAG (Retrieval-Augmented Generation) pattern with vector databases for semantic memory retrieval.

## Core Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Main Window │  │ Desktop Duck │  │  Chat Widget │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
└─────────┼─────────────────┼─────────────────┼───────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Game Logic Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          DuckTamagotchi (Core Game Logic)            │  │
│  │  - State Management  - Stat Tracking  - Save/Load    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    ML/AI Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Observer   │  │ Personality  │  │ Chat Service │      │
│  │              │  │   Engine     │  │              │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              RAG Service                              │  │
│  │  - Memory Retrieval  - Context Building              │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Vector Store (ChromaDB)                  │  │
│  │  - Embeddings  - Semantic Search  - Memory Storage    │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              LLM Service (Ollama)                     │  │
│  │  - Text Generation  - JSON Generation  - Chat        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Game Logic Layer

**File**: `duck_tamagotchi.py`

**Responsibilities**:
- Game state management (egg/duck stages)
- Stat tracking (hunger, happiness, health, energy, cleanliness)
- Time-based decay mechanics
- Save/load functionality
- State transitions (idle, walking, eating, etc.)

**Key Classes**:
- `DuckTamagotchi`: Main game logic class
- `DuckState`: Enum for duck states
- `GameStage`: Enum for game progression

### 2. ML/AI Layer

#### 2.1 Observer Pattern

**File**: `personality/observer.py`

**Purpose**: Observes game events and creates memories in the vector store.

**Event Types**:
- `user_fed_duck`: User feeds the duck
- `user_played_with_duck`: User plays with duck
- `user_cleaned_duck`: User cleans duck
- `duck_slept`: Duck sleeps
- `chat_message`: User chats with duck
- `naming_event`: Duck is named

**Memory Format**:
```python
{
    "document": "User fed duck when hunger was low (30%)",
    "event_type": "user_fed_duck",
    "metadata": {
        "timestamp": "2024-01-01T12:00:00",
        "stats_snapshot": {"hunger": 30, "happiness": 50, ...},
        "user_action": "fed"
    }
}
```

#### 2.2 Vector Store

**File**: `memory/vector_store.py`

**Technology**: ChromaDB (embedded vector database)

**Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- 384-dimensional vectors
- Fast inference (~10-50ms per embedding)
- Good semantic understanding

**Operations**:
- `add_memory()`: Store new memory with embedding
- `search_similar()`: Semantic similarity search
- `get_memories_by_event_type()`: Filter by event type
- `get_recent_memories()`: Get latest memories

**Storage**:
- Persistent storage in `chroma_db/` directory
- Embeddings computed on-the-fly using sentence-transformers
- Metadata stored alongside embeddings for filtering

#### 2.3 RAG Service

**File**: `llm/rag_service.py`

**Purpose**: Retrieval-Augmented Generation - builds context for LLM prompts.

**Key Methods**:
- `retrieve_relevant_memories()`: Semantic search for similar memories
- `build_context_for_personality()`: Context for personality generation
- `build_context_for_chat()`: Context for chat responses
- `summarize_memories()`: Create text summary from memories

**RAG Flow**:
1. User interaction occurs
2. Observer creates memory → stored in vector DB
3. Query time: RAG service searches for relevant memories
4. Context built from retrieved memories
5. Context included in LLM prompt
6. LLM generates response with context awareness

#### 2.4 Personality Engine

**File**: `personality/personality_engine.py`

**Purpose**: Generate and update duck personality based on observations.

**Personality Structure**:
```python
{
    "playfulness": 0.5,      # 0.0-1.0
    "independence": 0.5,     # 0.0-1.0
    "social": 0.5,           # 0.0-1.0
    "preferences": {
        "favorite_activity": "eating",
        "preferred_time": "afternoon",
        "dislikes": []
    },
    "quirks": ["loves swimming", "hates being dirty"],
    "personality_description": "A friendly, playful duck..."
}
```

**Generation Process**:
1. Collect relevant memories via RAG (last 15 memories)
2. Build prompt with memories, current stats, few-shot examples
3. LLM generates JSON personality
4. Merge with existing personality (weighted average for smooth transitions)
5. Save to `duck_personality.json`

**Update Frequency**:
- Initial generation: After 3+ memories
- Periodic updates: Every 5 new memories
- Force regeneration: On user request

#### 2.5 Chat Service

**File**: `chat/chat_service.py`

**Purpose**: Handle natural language chat with personality-aware responses.

**Flow**:
1. User sends message
2. Topic filter classifies message (on-topic vs off-topic)
3. If on-topic:
   - RAG retrieves relevant memories
   - Personality retrieved
   - LLM generates response with context
   - Response post-processed (length limits, formatting)
4. If off-topic:
   - Return redirect message

**Response Characteristics**:
- Short (1-2 sentences)
- Personality-aware (uses personality traits)
- Context-aware (uses relevant memories)
- Natural language with duck mannerisms

#### 2.6 Topic Filter

**File**: `chat/topic_filter.py`

**Purpose**: Classify messages as duck-related or off-topic.

**Method**: LLM-based classification
- Prompt includes examples of on-topic vs off-topic
- Returns classification + confidence score
- Threshold: 0.7 confidence for on-topic

**On-Topic Examples**:
- "How are you feeling?"
- "Do you like swimming?"
- "You seem happy today!"

**Off-Topic Examples**:
- "What's the capital of France?"
- "Tell me about quantum physics"
- "How do I fix my computer?"

#### 2.7 LLM Service

**File**: `llm/llm_service.py`

**Purpose**: Interface to Ollama LLM API.

**Backend**: Ollama (local LLM server)
- Default model: `llama3.1:8b`
- API endpoint: `http://localhost:11434`

**Methods**:
- `generate()`: Text generation
- `generate_json()`: JSON generation with parsing
- `is_available()`: Check if Ollama is running

**Configuration**:
- Temperature: 0.7 (default)
- Max tokens: 512 (default)
- Stop sequences: `["\n\n", "##", "Task:"]`

## Data Flow Examples

### Example 1: User Feeds Duck

```
1. User clicks "Feed" button
   ↓
2. DuckTamagotchi.feed() called
   - Updates hunger stat
   - Updates happiness stat
   ↓
3. Observer.observe_feeding_event() called
   - Creates memory document: "User fed duck when hunger was 30%"
   - Captures stats snapshot
   ↓
4. VectorStore.add_memory() called
   - Generates embedding using sentence-transformers
   - Stores in ChromaDB with metadata
   ↓
5. Personality Engine checks if update needed
   - If 5+ new memories: triggers personality update
   - RAG retrieves relevant memories
   - LLM generates updated personality
```

### Example 2: User Chats with Duck

```
1. User types: "How are you feeling?"
   ↓
2. ChatService.process_message() called
   ↓
3. TopicFilter.classify_message()
   - LLM classifies: "duck_related" (confidence: 0.9)
   - Returns: (True, 0.9)
   ↓
4. Observer.observe_chat_message()
   - Stores chat message as memory
   ↓
5. RAGService.build_context_for_chat()
   - Searches for similar memories: "duck feelings", "emotional state"
   - Retrieves 5 relevant memories
   ↓
6. PersonalityEngine.get_personality()
   - Retrieves current personality traits
   ↓
7. ChatService._generate_response()
   - Builds prompt with:
     * User message
     * Personality traits
     * Relevant memories
     * Duck stats
   - LLM generates response
   ↓
8. Post-processing
   - Limits to 2 sentences
   - Adds duck mannerisms (*quacks*)
   - Returns: "I'm feeling great! The swimming earlier was fun! *quacks happily*"
```

## Design Patterns

### 1. Observer Pattern
- `Observer` class observes game events
- Decouples game logic from memory storage
- Easy to add new event types

### 2. Service Layer Pattern
- Separate services for different concerns:
  - `LLMService`: LLM operations
  - `RAGService`: Memory retrieval
  - `ChatService`: Chat handling
  - `PersonalityEngine`: Personality logic

### 3. Repository Pattern
- `VectorStore` abstracts database operations
- Can swap ChromaDB for other vector DBs

### 4. Strategy Pattern
- Different prompt strategies for different tasks:
  - Personality generation prompts
  - Chat response prompts
  - Topic classification prompts

## Performance Considerations

### Vector Database
- **Embedding Generation**: Computed on-the-fly (no pre-computation)
- **Search Performance**: O(n) for small datasets, optimized for larger
- **Memory Usage**: ~1KB per memory (embedding + metadata)

### LLM Calls
- **Caching**: Personality cached until update needed
- **Batching**: Not currently implemented (could batch multiple requests)
- **Timeout**: 120 seconds for LLM calls

### Optimization Opportunities
1. **Embedding Caching**: Cache embeddings for frequently accessed memories
2. **Batch LLM Calls**: Batch multiple personality updates
3. **Async Operations**: Make LLM calls async to avoid blocking UI
4. **Indexing**: Add indexes for common queries (event_type, timestamp)

## Extensibility

### Adding New Event Types
1. Add event type to `Observer` class
2. Create observation method
3. Update memory format if needed
4. Add to personality prompt if relevant

### Adding New Personality Traits
1. Update `DEFAULT_PERSONALITY` in `PersonalityEngine`
2. Update personality prompt to include new trait
3. Update UI display if needed

### Switching LLM Backend
1. Implement new backend in `LLMService`
2. Update `_generate_ollama()` to use new API
3. Update configuration

### Using Different Vector DB
1. Implement new `VectorStore` subclass
2. Implement required methods:
   - `add_memory()`
   - `search_similar()`
   - `get_memories_by_event_type()`
3. Update initialization code

## Security Considerations

- **Local LLM**: All LLM operations run locally (Ollama)
- **No External APIs**: No data sent to external services
- **Local Storage**: All data stored locally
- **No User Data Collection**: No telemetry or user tracking

## Testing Strategy

### Unit Tests
- Test each service independently
- Mock LLM calls for fast tests
- Test vector store operations

### Integration Tests
- Test full RAG flow
- Test personality generation end-to-end
- Test chat flow

### Performance Tests
- Benchmark embedding generation
- Benchmark semantic search
- Benchmark LLM response times

## Future Enhancements

1. **Multi-modal Support**: Add image understanding for duck interactions
2. **Emotion Recognition**: Analyze user sentiment from chat
3. **Predictive Behavior**: Predict user actions based on patterns
4. **Multi-duck Support**: Support multiple ducks with different personalities
5. **Cloud Sync**: Optional cloud backup of memories
6. **Advanced RAG**: Implement re-ranking, multi-query retrieval
7. **Fine-tuning**: Fine-tune LLM on duck-specific data
