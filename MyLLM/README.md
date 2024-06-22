# My LLM

## an initial attempt at making my own LLM work environment

### Setting up Docker compose `docker-compose.yml`

```yaml
version: '3.8'

services:
  cli-tool:
    build: .
    env_file:
      - .env
    command: ["--model", "${MODEL_NAME}", "--token", "${HF_API_TOKEN}"]
```

### The initial python script `myllm.py`

#### downloads an image as defined in the .env file

```python
import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_model(model_name, api_token):
    logger.info("Authenticating with Hugging Face...")
    login(token=api_token)
    logger.info("Authentication successful.")
    
    logger.info(f"Downloading tokenizer for model: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, token=api_token)
    logger.info("Tokenizer downloaded successfully.")
    
    logger.info(f"Downloading model: {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(model_name, token=api_token)
    logger.info("Model downloaded successfully.")
    
    return tokenizer, model

def generate_response(model, tokenizer, prompt, max_length=36768):
    logger.info("Generating response...")
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(inputs["input_ids"], max_length=max_length, num_return_sequences=1, num_beams=5)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    logger.info("Response generation complete.")
    return response

def chat(model, tokenizer):
    print("Interactive chat session started. Type 'exit' to end the session.")
    while True:
        prompt = input("You: ")
        if prompt.lower() == 'exit':
            print("Exiting chat session.")
            break
        response = generate_response(model, tokenizer, prompt)
        print(f"Bot: {response}")

def main():
    parser = argparse.ArgumentParser(description="Simple CLI for Hugging Face models")
    parser.add_argument("--model", type=str, required=True, help="Hugging Face model name")
    parser.add_argument("--token", type=str, required=True, help="Hugging Face API token")
    args = parser.parse_args()

    logger.info(f"Downloading model: {args.model}...")
    tokenizer, model = download_model(args.model, args.token)
    logger.info("Model downloaded successfully.")

    chat(model, tokenizer)

if __name__ == "__main__":
    main()
```

### Dockerfile for the myllm.py app

```Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified
RUN pip install --no-cache-dir transformers torch sentencepiece protobuf

# Define the command to run the CLI tool
ENTRYPOINT ["python", "myllm.py"]
```

### Steps to Build and Run the Docker Container

1. **Ensure the `.env` file is correctly set up**:
   Ensure you have the `.env` file in the same directory as your `docker-compose.yml` with the correct values:

```env
MODEL_NAME=mistralai/Codestral-22B-v0.1
HF_API_TOKEN=your_huggingface_api_token  # Replace with your actual Hugging Face API token
```

2. **Build the Docker Image**:
   Open a terminal in the directory containing your files and run the following command to build the Docker image:

   ```bash
   docker-compose build
   ```

3. **Run the Docker Container**:
   Run the container with Docker Compose:

   ```bash
   docker-compose up
   ```

### Using the Interactive Chat

- Once the Docker container is running, you will enter an interactive chat session.
- Type your questions at the prompt and receive responses from the model.
- Type `exit` to end the chat session and stop the container.

This setup should allow for an interactive session without needing to restart the Docker container for each query. Let me know how the testing goes and if you encounter any issues.
