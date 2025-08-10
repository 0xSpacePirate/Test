import os
from dotenv import load_dotenv

load_dotenv()

# --- OpenAI Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Application Settings ---
# Database for Semantic Search
CHROMA_PERSIST_DIRECTORY = "local_chroma_db"
COLLECTION_NAME = "document_store"

# Database for Keyword Search (NEW)
KEYWORD_DB_PATH = "keyword_search.db"

# LangChain Settings
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 250
