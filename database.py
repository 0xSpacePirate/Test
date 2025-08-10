from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from config import CHROMA_PERSIST_DIRECTORY, COLLECTION_NAME, OPENAI_API_KEY


def get_vector_store():
    """Initializes and returns a persistent Chroma vector store."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in the environment.")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIRECTORY
    )
    return vector_store


def get_indexed_files():
    """
    Retrieves a set of all unique 'source' filenames from the vector database metadata.
    """
    try:
        vector_store = get_vector_store()
        # The 'get' method with no IDs/where clause returns all entries.
        existing_entries = vector_store.get()

        # Check if metadata exists and is a list
        if "metadatas" in existing_entries and existing_entries["metadatas"]:
            # Extract the 'source' from each metadata dictionary
            return {metadata['source'] for metadata in existing_entries["metadatas"] if 'source' in metadata}
        else:
            return set()

    except Exception as e:
        # This can happen if the DB doesn't exist yet, which is fine on first run.
        print(f"Could not get indexed files (this is normal on first run): {e}")
        return set()
