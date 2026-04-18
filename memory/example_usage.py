"""
Example usage of the VectorStore for Chroma database.

This demonstrates how to set up and use the vector store for storing
and retrieving duck memories.
"""
from memory.vector_store import VectorStore
from datetime import datetime


def example_basic_usage():
    """Basic example of using the vector store"""
    
    # Initialize with persistent storage
    # Data will be saved in "chroma_db" directory
    print("Initializing vector store...")
    vector_store = VectorStore(persist_directory="chroma_db")
    
    # Add some example memories
    print("\nAdding memories...")
    
    # Memory 1: User fed duck
    vector_store.add_memory(
        document="User fed the duck when hunger was low at 25%. Duck was very happy.",
        event_type="user_fed_duck",
        stats_snapshot={
            "hunger": 25,
            "happiness": 80,
            "health": 95,
            "energy": 70,
            "cleanliness": 85
        },
        user_action="fed_duck",
        metadata={"time_of_day": "morning"}
    )
    
    # Memory 2: Duck interacted with pond
    vector_store.add_memory(
        document="Duck swam in the pond. This increased happiness and cleanliness.",
        event_type="item_interaction",
        stats_snapshot={
            "hunger": 60,
            "happiness": 90,
            "health": 100,
            "energy": 50,
            "cleanliness": 95
        },
        user_action="placed_pond",
        metadata={"item_type": "pond", "duration_seconds": 3}
    )
    
    # Memory 3: User played with duck
    vector_store.add_memory(
        document="User played with the duck. Duck was energetic and playful.",
        event_type="user_played_with_duck",
        stats_snapshot={
            "hunger": 70,
            "happiness": 95,
            "health": 100,
            "energy": 40,
            "cleanliness": 80
        },
        user_action="played_with_duck"
    )
    
    print(f"Total memories stored: {vector_store.get_memory_count()}")
    
    # Search for similar memories
    print("\nSearching for memories about feeding...")
    results = vector_store.search_similar(
        query="user feeding the duck when hungry",
        n_results=3
    )
    
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"  Document: {result['document']}")
        print(f"  Event Type: {result['metadata']['event_type']}")
        print(f"  Timestamp: {result['metadata']['timestamp']}")
        if 'distance' in result:
            print(f"  Similarity Distance: {result['distance']:.4f}")
    
    # Get memories by event type
    print("\n\nGetting all feeding events...")
    feeding_memories = vector_store.get_memories_by_event_type("user_fed_duck")
    print(f"Found {len(feeding_memories)} feeding memories")
    
    # Get recent memories
    print("\n\nGetting 5 most recent memories...")
    recent = vector_store.get_recent_memories(limit=5)
    for i, memory in enumerate(recent, 1):
        print(f"{i}. [{memory['metadata']['event_type']}] {memory['document'][:60]}...")
    
    print("\nExample completed!")


def example_in_memory():
    """Example using in-memory database (data not persisted)"""
    
    print("\n\n=== In-Memory Example ===")
    print("Initializing in-memory vector store...")
    vector_store = VectorStore()  # No persist_directory = in-memory
    
    # Add a memory
    vector_store.add_memory(
        document="Test memory in in-memory database",
        event_type="test_event",
        user_action="test"
    )
    
    print(f"Memory count: {vector_store.get_memory_count()}")
    print("Note: This data will be lost when the program exits")


if __name__ == "__main__":
    # Run examples
    example_basic_usage()
    example_in_memory()
