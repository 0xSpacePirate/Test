import psycopg2
import os
import time
import sys

conn_params = {
    'host': os.getenv('PG_HOST', 'postgres'),
    'port': int(os.getenv('PG_PORT', 5432)),
    'dbname': os.getenv('PG_DB', 'postgres'),
    'user': os.getenv('PG_USER', 'postgres'),
    'password': os.getenv('PG_PASSWORD', 'postgres')
}

def wait_for_postgres(conn_params, max_retries=30, delay=2):
    """Wait for PostgreSQL to be ready"""
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to PostgreSQL... (attempt {attempt + 1}/{max_retries})")
            conn = psycopg2.connect(**conn_params)
            conn.close()
            print("Successfully connected to PostgreSQL!")
            return True
        except psycopg2.OperationalError as e:
            print(f"Connection failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. PostgreSQL is not available.")
                return False
    return False

def read_file_flexible(filepath):
    encodings = ['utf-8', 'cp1251', 'latin1']  # add more if you want
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    # If all fail, read ignoring errors (may cause some character loss)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def insert_file_to_postgres(filepath, conn_params):
    content = read_file_flexible(filepath)

    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    print("CONTENT = " + content)

    insert_query = """
    INSERT INTO public.documents (filename, content)
    VALUES (%s, %s)
    """

    cur.execute(insert_query, (filepath, content))
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    print("Starting...")
    print("conn_params: ", conn_params)

    if not wait_for_postgres(conn_params):
        print("Failed to connect to PostgreSQL. Exiting.")
        sys.exit(1)

    filepath = os.getenv('FILE_PATH', '/app/test.doc')
    
    try:
        insert_file_to_postgres(filepath, conn_params)
        print(f"Inserted '{filepath}' into PostgreSQL")
    except Exception as e:
        print(f"Error inserting file: {e}")
        sys.exit(1)