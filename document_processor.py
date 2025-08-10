import os
import pathlib
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP
from database import get_vector_store, get_indexed_files as get_chroma_indexed_files
# Import the new keyword engine functions
from keyword_search_engine import insert_file_to_sqlite


def process_and_ingest_documents(status_callback, source_directory):
    """
    Finds new files and ingests them into BOTH the ChromaDB for semantic search
    AND the SQLite DB for keyword search.
    """
    if not source_directory or not os.path.isdir(source_directory):
        status_callback("Error: Please select a valid document directory first.")
        return

    status_callback("Initializing vector store...")
    vector_store = get_vector_store()

    status_callback("Checking for already indexed files...")
    # We use ChromaDB as the source of truth for what's been indexed.
    indexed_files = get_chroma_indexed_files()
    status_callback(f"Found {len(indexed_files)} files already in semantic database.")

    source_path = pathlib.Path(source_directory)
    doc_files = list(source_path.glob("**/*.doc"))
    docx_files = list(source_path.glob("**/*.docx"))
    all_word_files = doc_files + docx_files

    if not all_word_files:
        status_callback("No .doc or .docx files found in the selected directory.")
        return

    files_to_process = [f for f in all_word_files if str(f.resolve()) not in indexed_files]

    if not files_to_process:
        status_callback("No new documents to process.")
        return

    status_callback(f"Found {len(files_to_process)} new documents to index for both systems.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    for i, doc_path in enumerate(files_to_process):
        try:
            full_path_str = str(doc_path.resolve())
            status_callback(f"Processing ({i + 1}/{len(files_to_process)}): {doc_path.name}")

            # 1. Load the document text ONCE
            loader = UnstructuredWordDocumentLoader(full_path_str)
            documents = loader.load()
            full_content = "\n\n".join(doc.page_content for doc in documents)

            # 2. Ingest into Keyword Search DB (SQLite)
            status_callback("  -> Indexing for keyword search...")
            insert_file_to_sqlite(full_path_str, full_content)

            # 3. Ingest into Semantic Search DB (Chroma)
            status_callback("  -> Indexing for semantic search...")
            for doc in documents:
                doc.metadata['source'] = full_path_str

            chunks = text_splitter.split_documents(documents)
            vector_store.add_documents(chunks)

            status_callback(f"  -> Successfully indexed {doc_path.name} in both systems.")
        except Exception as e:
            status_callback(f"  -> FAILED to process {doc_path.name}: {e}")

    # Persist all Chroma changes at the end of the batch
    status_callback("Persisting semantic data...")
    vector_store.persist()
    status_callback("Ingestion complete.")
