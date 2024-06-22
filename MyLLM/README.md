# MyLLM

## An Advanced LLM Work Environment

MyLLM is a sophisticated project that allows you to download, load, and interact with various language models from Hugging Face. It provides a flexible and user-friendly interface for working with large language models in a containerized environment.

## Features

- Download models from Hugging Face
- Load models with different quantizations
- Interactive chat session with loaded models
- Configurable logging and model parameters
- Docker-based deployment for easy setup and portability

## Project Structure

- `myllm.py`: Main Python script for the application
- `config.yaml`: Configuration file for the application
- `docker-compose.yml`: Docker Compose file for running the application
- `requirements.txt`: List of Python dependencies
- `Dockerfile`: Dockerfile for building the application image
- `build_base_image.sh`: Script for building the base Docker image

## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- NVIDIA GPU with CUDA support (for GPU acceleration)

### Building the Base Image

1. Make the build script executable:
   ```
   chmod +x build_base_image.sh
   ```

2. Run the build script:
   ```
   ./build_base_image.sh
   ```

This script builds a base image with optimized settings for your system. It uses 36 cores and 200GB of memory for the build process.

### Configuration

1. Edit `config.yaml` to set your Hugging Face API token and other preferences:

   ```yaml
   huggingface:
     api_token: your_api_token_here
     models_dir: /models

   logging:
     level: INFO
     format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

   model_defaults:
     max_length: 2048
     num_beams: 3
     early_stopping: true
   ```

2. Ensure your `docker-compose.yml` file is set up correctly:

   ```yaml
   version: '3.8'

   services:
     cli-tool:
       build:
         context: .
         dockerfile: Dockerfile
       image: myllm-app:latest
       environment:
         - HF_API_TOKEN
       volumes:
         - ./models:/models
         - ./config.yaml:/app/config.yaml
       user: "1000:1000"
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: all
                 capabilities: [gpu]
       stdin_open: true
       tty: true
       entrypoint: ["python", "-u", "myllm.py"]
   ```

## Usage

1. Start the application:
   ```
   docker-compose up
   ```

2. Once the application is running, you'll be presented with a menu:
   - Download a model
   - Load a model
   - Exit

3. To download a model:
   - Choose option 1
   - Enter the model name (e.g., "mistralai/Codestral-22B-v0.1")

4. To load a model and start a chat session:
   - Choose option 2
   - Select a model from the list
   - Choose a quantization option
   - Start chatting with the model

5. To exit the application, choose option 3 from the main menu.

## Customization

- Modify `config.yaml` to change logging settings, model defaults, or the Hugging Face API token.
- Edit `myllm.py` to add new features or modify existing functionality.
- Adjust `docker-compose.yml` to change container settings or resource allocations.

## Troubleshooting

- If you encounter issues with model downloads, ensure your Hugging Face API token is correct in `config.yaml`.
- For performance issues, try adjusting the resource allocations in `docker-compose.yml`.
- Check the application logs for detailed error messages and debugging information.

## Contributing

Contributions to MyLLM are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

[Add your chosen license here]