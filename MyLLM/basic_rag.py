import os
import requests
import yaml
import numpy as np
from pathlib import Path
import faiss

# Load configuration
def load_config(config_path='config.yaml'):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

# Initialize the vector store
def init_faiss_store(dim):
    index = faiss.IndexFlatL2(dim)  # Use L2 distance
    return index

# Function to get embeddings using the OpenAI-compliant API
def get_local_model_embedding(text, model_name):
    url = "http://localhost:11434/v1/embeddings"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model_name,
        "input": text
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    # Print the response for debugging
    print("API Response:", response.json())
    
    if response.status_code == 200:
        # Extract the first embedding from the response data
        embeddings = response.json().get("data", [])[0].get("embedding", [])
        if not embeddings:
            raise ValueError("Received empty embedding from the API.")
        return np.array(embeddings)
    else:
        raise RuntimeError(f"Error fetching embedding: {response.text}")

# Parse files and generate embeddings
def process_files(directory, model_name):
    embeddings = []
    file_paths = []
    
    # Traverse the directory recursively
    for file_path in Path(directory).rglob('*'):
        print(f"Found file: {file_path}")
        if file_path.suffix in ['.txt', '.md']:
            print(f"Processing file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            embedding = get_local_model_embedding(content, model_name)
            embeddings.append(embedding)
            file_paths.append(str(file_path))
        else:
            print(f"Skipping file: {file_path}")

    return np.array(embeddings), file_paths

# Add embeddings to the vector store
def add_to_vector_store(index, embeddings, file_paths):
    # Convert embeddings to numpy array of type float32
    embeddings = np.array(embeddings, dtype=np.float32)
    
    # Debug: Print embedding shape and type
    print(f"Embedding shape: {embeddings.shape}, dtype: {embeddings.dtype}")
    
    # Add embeddings to the FAISS index
    index.add(embeddings)
    
    return index, file_paths

# Retrieve documents based on query
def search(query, model_name, index, file_paths, k=5):
    # Get the query embedding
    query_embedding = get_local_model_embedding(query, model_name)
    
    # Convert to a numpy array of type float32 and ensure correct shape
    query_embedding = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
    
    # Perform the search
    distances, indices = index.search(query_embedding, k)
    
    # Return the results
    results = [(file_paths[i], distances[0][j]) for j, i in enumerate(indices[0])]
    return results


def main():
    # Load config
    config = load_config()

    # Simple test to ensure embedding generation works
    test_input = "This is a test sentence."
    print("Testing embedding generation with simple input:")
    print(get_local_model_embedding(test_input, config['embedding']['model_name']))

    # Initialize vector store
    vector_store = init_faiss_store(config['embedding']['dimension'])

    # Process files and populate the vector store
    embeddings, file_paths = process_files(config['paths']['documents_directory'], config['embedding']['model_name'])
    vector_store, file_paths = add_to_vector_store(vector_store, embeddings, file_paths)

    # Example search
    query = "sample query to test retrieval"
    results = search(query, config['embedding']['model_name'], vector_store, file_paths)
    
    print("Search results:")
    for result in results:
        print(f"File: {result[0]}, Distance: {result[1]}")

if __name__ == "__main__":
    main()
