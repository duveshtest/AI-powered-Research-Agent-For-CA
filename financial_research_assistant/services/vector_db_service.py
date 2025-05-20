# services/vector_db_service.py
import chromadb
import uuid # For generating unique IDs for documents

# Initialize a ChromaDB client.
# For now, we'll use an in-memory client (EphemeralClient).
# For persistence, one would use HttpClient or PersistentClient.
# client = chromadb.Client() # This defaults to EphemeralClient, which is fine for now.
# More explicitly:
client = chromadb.EphemeralClient() # In-memory, no data saved on disk across runs.
# Or, to persist to disk:
# client = chromadb.PersistentClient(path="./chroma_db_data") # Data will be saved in this directory

# Using a default embedding function that comes with ChromaDB (Sentence Transformers all-MiniLM-L6-v2)
# This is convenient as it doesn't require setting up a separate embedding model for now.
# For more control or different models, one might specify an embedding_function.
# e.g., from chromadb.utils import embedding_functions
# default_ef = embedding_functions.DefaultEmbeddingFunction()

COLLECTION_NAME = "financial_reports_content"
collection = None

def get_or_create_collection(name=COLLECTION_NAME):
    """
    Gets an existing collection or creates it if it doesn't exist.
    Uses the default Sentence Transformers embedding function.
    """
    global collection
    if collection is not None and collection.name == name:
        return collection
    try:
        collection = client.get_or_create_collection(
            name=name,
            # metadata={"hnsw:space": "cosine"} # Optional: configure collection metadata, e.g., distance metric
        )
        print(f"[VectorDBService] Collection '{name}' loaded/created successfully.")
        return collection
    except Exception as e:
        print(f"[VectorDBService] Error getting or creating collection '{name}': {e}")
        # Depending on the error, one might want to reset the client or raise the exception
        # For example, if the database is corrupted or inaccessible.
        # For an EphemeralClient, client.reset() might be an option before retrying,
        # but this would lose all in-memory data.
        # client.reset() # Use with caution, clears all data from the client.
        raise # Re-raise the exception to make the caller aware of the issue.


def add_texts_to_collection(texts: list[str], metadatas: list[dict] = None, ids: list[str] = None):
    """
    Adds texts (and optional metadatas) to the ChromaDB collection.

    Args:
        texts (list[str]): A list of text strings to add.
        metadatas (list[dict], optional): A list of dictionaries, one for each text, containing metadata.
                                           Example: [{"source_url": "http://example.com/doc1"}, ...]
        ids (list[str], optional): A list of unique IDs for each text. If None, UUIDs will be generated.

    Returns:
        bool: True if successful, False otherwise.
    """
    current_collection = get_or_create_collection()
    if not current_collection:
        return False

    if not texts:
        print("[VectorDBService] No texts provided to add.")
        return False

    if ids is None:
        ids = [str(uuid.uuid4()) for _ in texts]
    elif len(ids) != len(texts):
        print("[VectorDBService] Error: Number of IDs must match number of texts.")
        return False

    if metadatas is None:
        # Create empty metadata if none provided, as ChromaDB expects it (can be empty dicts)
        metadatas = [{} for _ in texts]
    elif len(metadatas) != len(texts):
        print("[VectorDBService] Error: Number of metadatas must match number of texts.")
        return False
    
    # Ensure all metadata values are of supported types (str, int, float, bool)
    for i, meta in enumerate(metadatas):
        for key, value in meta.items():
            if not isinstance(value, (str, int, float, bool)):
                print(f"[VectorDBService] Warning: Metadata value for key '{key}' in document {ids[i]} is not a supported type ({type(value)}). Converting to string.")
                metadatas[i][key] = str(value)


    try:
        current_collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        print(f"[VectorDBService] Successfully added {len(texts)} documents to collection '{current_collection.name}'.")
        return True
    except Exception as e:
        # More specific exception handling can be added here (e.g., for chromadb.errors.DuplicateIDError)
        print(f"[VectorDBService] Error adding documents to collection: {e}")
        return False

def query_collection(query_texts: list[str], n_results: int = 5, where_filter: dict = None):
    """
    Queries the collection for texts similar to the query_texts.

    Args:
        query_texts (list[str]): A list of query texts.
        n_results (int, optional): The number of results to return for each query text. Defaults to 5.
        where_filter (dict, optional): A dictionary for filtering results based on metadata.
                                   Example: {"source_url": "http://example.com/doc1"}

    Returns:
        dict: A dictionary containing the query results (documents, metadatas, distances, etc.),
              or None if an error occurs.
              The structure is typically like:
              {
                  'ids': [[id1, id2, ...]],
                  'documents': [[doc1, doc2, ...]],
                  'metadatas': [[meta1, meta2, ...]],
                  'distances': [[dist1, dist2, ...]]
              }
    """
    current_collection = get_or_create_collection()
    if not current_collection:
        return None
        
    if not query_texts:
        print("[VectorDBService] No query texts provided.")
        return None

    try:
        results = current_collection.query(
            query_texts=query_texts,
            n_results=min(n_results, current_collection.count()), # Cannot request more results than exist in collection
            where=where_filter
            # One can also include 'embeddings' if needed.
        )
        # print(f"[VectorDBService] Query results: {results}")
        return results
    except Exception as e:
        print(f"[VectorDBService] Error querying collection: {e}")
        return None

def count_collection_items():
    """Returns the number of items in the collection."""
    current_collection = get_or_create_collection()
    if not current_collection:
        return 0
    return current_collection.count()

def clear_collection(name=COLLECTION_NAME):
    """Deletes all items from a collection (if it exists) or deletes the collection itself."""
    global collection
    try:
        print(f"[VectorDBService] Attempting to clear collection '{name}'...")
        # client.delete_collection(name=name) # This deletes the collection itself
        # To just clear items but keep the collection:
        # We can get all items and delete by ID, or recreate it.
        # Recreating is simpler for EphemeralClient.
        client.delete_collection(name=name)
        collection = client.get_or_create_collection(name=name) # Recreate it empty
        print(f"[VectorDBService] Collection '{name}' cleared and recreated.")
        return True
    except Exception as e:
        # Catch specific errors if needed, e.g. if collection doesn't exist.
        print(f"[VectorDBService] Error clearing collection '{name}': {e}. It might not exist.")
        # If it didn't exist, try to create it anyway to ensure it's usable
        try:
            collection = client.get_or_create_collection(name=name)
            return True
        except Exception as e_create:
            print(f"[VectorDBService] Error ensuring collection '{name}' exists after clear attempt: {e_create}")
            return False


if __name__ == '__main__':
    # Example Usage:
    # To run this test, navigate to the 'financial_research_assistant' directory
    # and run: python -m services.vector_db_service

    print("\n--- VectorDBService Test ---")
    
    # Ensure collection is clean for testing
    print(f"Initial collection count: {count_collection_items()}")
    clear_collection()
    print(f"Collection count after clearing: {count_collection_items()}")

    sample_texts = [
        "Apple Inc. reported strong Q4 earnings in 2023.",
        "Microsoft Azure is gaining market share in cloud computing.",
        "Google's Pixel 8 features advanced AI capabilities.",
        "The new AI regulations might impact tech companies.",
        "Apple's Vision Pro is a new mixed reality headset."
    ]
    sample_metadatas = [
        {"source_url": "apple_earnings_report.com", "year": 2023, "company": "Apple"},
        {"source_url": "cloud_market_analysis.com", "year": 2023, "company": "Microsoft"},
        {"source_url": "pixel8_review.com", "year": 2023, "company": "Google"},
        {"source_url": "ai_regulations_news.com", "year": 2023, "topic": "AI"},
        {"source_url": "vision_pro_launch.com", "year": 2023, "company": "Apple", "product": "Vision Pro"}
    ]
    sample_ids = [f"doc{i}" for i in range(len(sample_texts))]

    print("\nAdding documents to collection...")
    success = add_texts_to_collection(texts=sample_texts, metadatas=sample_metadatas, ids=sample_ids)
    if success:
        print(f"Current collection count: {count_collection_items()}")

        print("\nQuerying collection for 'Apple':")
        query_results_apple = query_collection(query_texts=["latest news about Apple"], n_results=2)
        if query_results_apple and query_results_apple.get('documents'):
            for i, doc in enumerate(query_results_apple['documents'][0]):
                print(f"  Result {i+1}: {doc}")
                print(f"    Metadata: {query_results_apple['metadatas'][0][i]}")
                print(f"    Distance: {query_results_apple['distances'][0][i]}")
        else:
            print("No results for 'Apple' or error occurred.")

        print("\nQuerying collection for 'AI' with filter for 'Google':")
        query_results_ai_google = query_collection(
            query_texts=["AI technology"],
            n_results=2,
            where_filter={"company": "Google"} # Filter for documents where metadata 'company' is 'Google'
        )
        if query_results_ai_google and query_results_ai_google.get('documents'):
            for i, doc in enumerate(query_results_ai_google['documents'][0]):
                print(f"  Result {i+1}: {doc}")
                print(f"    Metadata: {query_results_ai_google['metadatas'][0][i]}")
        else:
            print("No results for 'AI' at Google or error occurred.")
        
        print("\nQuerying with multiple texts:")
        multi_query_results = query_collection(query_texts=["Apple earnings", "Microsoft cloud"], n_results=1)
        if multi_query_results and multi_query_results.get('documents'):
            print("Results for 'Apple earnings':")
            if multi_query_results['documents'][0]: print(f"  - {multi_query_results['documents'][0][0]}")
            print("Results for 'Microsoft cloud':")
            if multi_query_results['documents'][1]: print(f"  - {multi_query_results['documents'][1][0]}")


    print("\nClearing collection again...")
    clear_collection()
    print(f"Collection count after final clear: {count_collection_items()}")
    print("--- Test End ---")
