import os
import pathlib
import sys
import traceback
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP
from database import get_indexed_files as get_chroma_indexed_files, get_vector_store
from keyword_search_engine import insert_file_to_sqlite


def process_and_ingest_documents(status_callback, source_directory):
    """
    Finds new files and ingests them into BOTH databases with aggressive error logging.
    """
    if not source_directory or not os.path.isdir(source_directory):
        status_callback("Error: Please select a valid document directory first.")
        return

    try:
        status_callback("Initializing vector store...")
        print("[DEBUG] Initializing vector store...")
        vector_store = get_vector_store()
        print("[DEBUG] Vector store initialized successfully.")

        status_callback("Checking for already indexed files...")
        print("[DEBUG] Checking for indexed files...")
        indexed_files = get_chroma_indexed_files()
        print(f"[DEBUG] Found {len(indexed_files)} indexed files.")

        source_path = pathlib.Path(source_directory)
        doc_files = list(source_path.glob("**/*.doc"))
        docx_files = list(source_path.glob("**/*.docx"))
        all_word_files = doc_files + docx_files

        status_callback(f"Found {len(all_word_files)} total .doc/.docx files in directory.")
        print(f"[DEBUG] Found {len(all_word_files)} total .doc/.docx files.")

        if not all_word_files:
            status_callback("No .doc or .docx files found. Ingestion finished.")
            return

        files_to_process = [f for f in all_word_files if str(f.resolve()) not in indexed_files]

        if not files_to_process:
            status_callback("No new documents to process. All files are already indexed.")
            return

        status_callback(f"Found {len(files_to_process)} new documents to index...")
        print(f"[DEBUG] Found {len(files_to_process)} new files to process.")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

        for i, doc_path in enumerate(files_to_process):
            full_path_str = str(doc_path.resolve())
            print(f"\n[DEBUG] --- Processing file {i + 1}: {full_path_str} ---")
            status_callback(f"Processing ({i + 1}/{len(files_to_process)}): {doc_path.name}")

            try:
                loader = UnstructuredWordDocumentLoader(full_path_str)
                documents = loader.load()
                full_content = "\n\n".join(doc.page_content for doc in documents)
                print(f"[DEBUG] Successfully loaded content from {doc_path.name}. Content length: {len(full_content)}")

                status_callback(f"  -> Indexing '{doc_path.name}' for keyword search...")
                insert_file_to_sqlite(full_path_str, full_content)
                print(f"[DEBUG] Indexed for keyword search.")

                status_callback(f"  -> Indexing '{doc_path.name}' for semantic search...")
                for doc in documents:
                    doc.metadata['source'] = full_path_str

                chunks = text_splitter.split_documents(documents)
                print(f"[DEBUG] Split into {len(chunks)} chunks.")

                vector_store.add_documents(chunks)
                print(f"[DEBUG] Added documents to vector store.")

                status_callback(f"  -> Successfully indexed {doc_path.name} in both systems.")

            except Exception as file_error:
                # This will catch an error on a specific file
                print(f"!!! FATAL ERROR PROCESSING FILE: {doc_path.name} !!!", file=sys.stderr)
                traceback.print_exc()
                status_callback(f"ERROR on file {doc_path.name}. See console for details.")
                # We continue to the next file
                continue

    except Exception as e:
        # This will catch a more general error (e.g., initializing the vector store)
        print("!!! FATAL ERROR IN process_and_ingest_documents !!!", file=sys.stderr)
        traceback.print_exc()
        status_callback(f"FATAL ERROR during ingestion: {e}")
        raise e

    status_callback("Ingestion complete.")
