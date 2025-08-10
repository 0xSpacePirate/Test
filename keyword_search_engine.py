import os
import sqlite3
from config import KEYWORD_DB_PATH # We will add this to config.py

def create_db():
    """Creates the SQLite database and tables if they don't exist."""
    try:
        conn = sqlite3.connect(KEYWORD_DB_PATH)
        c = conn.cursor()
        c.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(
            path,
            content,
            tokenize = 'porter unicode61'
        );
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Keyword DB error on create: {e}")

def insert_file_to_sqlite(filepath, content):
    """
    Inserts or replaces a document's full content for keyword searching.
    We use the full path as the unique identifier.
    """
    if not content or not content.strip():
        return
    try:
        conn = sqlite3.connect(KEYWORD_DB_PATH)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO documents (path, content) VALUES (?, ?)', (filepath, content))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"  -> FAILED to insert into keyword database: {e}")

def search_sqlite(query):
    """Performs a full-text search and returns a list of full document paths."""
    results = []
    try:
        conn = sqlite3.connect(KEYWORD_DB_PATH)
        c = conn.cursor()
        # The FTS5 query syntax allows for powerful matching.
        # Wrapping in quotes "" searches for phrases.
        c.execute("SELECT path FROM documents WHERE documents MATCH ?", (f'"{query}"',))
        results = [row[0] for row in c.fetchall()]
        conn.close()
    except sqlite3.Error as e:
        print(f"Keyword search error: {e}")
    return results
