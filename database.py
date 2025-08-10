from key_manager import load_credentials
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import CHROMA_PERSIST_DIRECTORY, COLLECTION_NAME


def get_vector_store():
    """
    Initializes the vector store, loading both the API key and Project ID
    and passing them correctly to the OpenAI client.
    """
    api_key, project_id = load_credentials()

    if not api_key or not project_id:
        raise ValueError("OpenAI credentials not found. Please set them in the Settings menu.")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=api_key,
        default_headers={
            "OpenAI-Project": project_id
        }
    )

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
        existing_entries = vector_store.get()

        if "metadatas" in existing_entries and existing_entries["metadatas"]:
            return {metadata['source'] for metadata in existing_entries["metadatas"] if 'source' in metadata}
        else:
            return set()

    except Exception:
        return set()
    