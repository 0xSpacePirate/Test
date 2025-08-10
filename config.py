import os
from dotenv import load_dotenv

load_dotenv()

# --- Application Settings ---
# Database for Semantic Search
CHROMA_PERSIST_DIRECTORY = "local_chroma_db"
COLLECTION_NAME = "document_store"

# Database for Keyword Search
KEYWORD_DB_PATH = "keyword_search.db"

# LangChain Settings
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 250