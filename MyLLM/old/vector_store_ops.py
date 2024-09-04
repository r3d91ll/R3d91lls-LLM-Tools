import os
import json
import psycopg2
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Database connection parameters
DB_NAME = os.getenv('POSTGRES_DB')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_HOST = os.getenv('POSTGRES_HOST')
DB_PORT = os.getenv('POSTGRES_PORT')

# Ollama API endpoint
OLLAMA_URL = "http://localhost:11434"

def get_embedding(text):
    """Get embedding from Ollama API"""
    try:
        response = requests.post(f"{OLLAMA_URL}/api/embed", json={
            "model": "llama2",
            "prompt": text
        })
        response.raise_for_status()
        return response.json()['embedding']
    except requests.RequestException as e:
        print(f"Error getting embedding: {e}")
        return None

def process_file(cursor, file_path):
    """Process a single file and store its embedding"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        embedding = get_embedding(content)
        if embedding is None:
            print(f"Failed to get embedding for {file_path}")
            return

        metadata = {
            "file_size": os.path.getsize(file_path),
            "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
        }

        cursor.execute("""
            INSERT INTO vector_store (filename, content, embedding, metadata)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (filename) DO UPDATE SET
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata,
                last_updated = CURRENT_TIMESTAMP
        """, (str(file_path), content, embedding, json.dumps(metadata)))

        print(f"Processed: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def similarity_search(cursor, query_text, num_results=5):
    query_embedding = get_embedding(query_text)
    if query_embedding is None:
        return []

    cursor.execute("""
        SELECT filename, content, metadata, embedding <=> %s AS distance
        FROM vector_store
        ORDER BY embedding <=> %s
        LIMIT %s
    """, (query_embedding, query_embedding, num_results))

    return cursor.fetchall()

def main(docs_directory):
    """Process all markdown files in the given directory"""
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    cursor = conn.cursor()

    try:
        for file_path in Path(docs_directory).rglob('*.md'):
            process_file(cursor, file_path)
        conn.commit()
        print("All documents processed successfully.")

        # Example similarity search
        search_query = "What is Ollama?"
        results = similarity_search(cursor, search_query)
        print(f"\nSearch results for query: '{search_query}'")
        for result in results:
            print(f"Filename: {result[0]}, Distance: {result[3]}")
            print(f"Content: {result[1][:100]}...")  # Print first 100 characters of content
            print(f"Metadata: {result[2]}")
            print("---")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    docs_directory = "/path/to/your/docs"  # Update this path
    main(docs_directory)
