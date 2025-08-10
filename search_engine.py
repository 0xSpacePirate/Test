from database import get_vector_store

def perform_search(query, status_callback):
    """
    Performs a simple similarity search in the vector store for the given query.
    """
    if not query:
        status_callback("Please enter a search query.")
        return []

    status_callback("Initializing vector store for search...")
    try:
        vector_store = get_vector_store()
    except Exception as e:
        status_callback(f"Error initializing vector store for search: {e}")
        return []

    status_callback(f"Searching for: '{query}'")
    try:
        # k=5 returns the top 5 most similar chunks (documents in LangChain terms)
        results = vector_store.similarity_search(query, k=5)
        status_callback(f"Search complete. Found {len(results)} potential matches.")
        return results
    except Exception as e:
        status_callback(f"An error occurred during search: {e}")
        return []
