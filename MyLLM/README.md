# MyLLM

## An Advanced LLM Work Environment

MyLLM is a sophisticated project that allows you to download, load, and interact with various language models from Hugging Face. It provides a flexible and user-friendly interface for working with large language models in a containerized environment.

## Features

- Download models from Hugging Face
- Load models with different quantizations
- Interactive chat session with loaded models
- Configurable logging and model parameters
- Docker-based deployment for easy setup and portability
- Automatic context length detection and setting
- Support for multiple quantization options per model
- User-friendly menu system for model selection and interaction

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

   ```bash
   chmod +x build_base_image.sh
   ```

2. Run the build script:

   ```bash
   ./build_base_image.sh
   ```

This script builds a base image with optimized settings for your system. By default, it uses 36 cores and 200GB of memory for the build process. You can modify these values in the script:

- `MAX_JOBS`: Number of CPU cores to use (default: 36)
- `--cpuset-cpus`: CPU core range to use (default: "0-35")
- `--memory`: Amount of RAM to allocate (default: 200g)

Adjust these values based on your system's capabilities.

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

   You can modify the following settings:
   - `api_token`: Your Hugging Face API token
   - `models_dir`: Directory to store downloaded models
   - `logging.level`: Logging verbosity (e.g., INFO, DEBUG, WARNING)
   - `model_defaults`: Default parameters for model generation
   - `model_defaults`: are there for when the myllm.py script is not able to figure out what those values should be

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

   You can adjust the following:
   - `user`: Change to match your system's user ID
   - `resources`: Modify GPU allocation if needed

   NOTE: that the models directory is for the models you download. Ensure that the directory exists within your Docker folder. This will ensure that any model you download is accessible outside of this particular container.

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

## Key Features in myllm.py

1. **Automatic Context Length Detection**:
   The script automatically detects the maximum sequence length (context length) for each model. If the information is available in the model's configuration, it uses that value. Otherwise, it falls back to the default specified in `config.yaml`.

   ```python
   if hasattr(model_config, 'max_position_embeddings'):
       max_length = model_config.max_position_embeddings
   else:
       max_length = config['model_defaults']['max_length']
   ```

2. **Multiple Quantization Support**:
   The script checks for available quantizations for each model and allows users to choose between them. This includes support for various quantization formats like .bin, .pt, and .gguf files.

   ```python
   quantizations = list_quantizations(model_name)
   ```

3. **Dynamic Model Loading**:
   Models are loaded with optimized settings, including automatic device mapping and half-precision floating point (float16) for improved performance and memory usage.

   ```python
   model = AutoModelForCausalLM.from_pretrained(model_path, device_map='auto', torch_dtype=torch.float16, trust_remote_code=True)
   ```

4. **Configurable Generation Parameters**:
   Users can adjust generation parameters in `config.yaml`, including `max_length`, `num_beams`, and `early_stopping`.

5. **Colored Logging**:
   The script uses colored logging for better readability and easier debugging.

## Customization

- Modify `config.yaml` to change logging settings, model defaults, or the Hugging Face API token.
- Edit `myllm.py` to add new features or modify existing functionality.
- Adjust `docker-compose.yml` to change container settings or resource allocations.
- Modify `build_base_image.sh` to adjust CPU and memory usage during the base image build process.

## Troubleshooting

- If you encounter issues with model downloads, ensure your Hugging Face API token is correct in `config.yaml`.
- For performance issues, try adjusting the resource allocations in `docker-compose.yml`.
- Check the application logs for detailed error messages and debugging information.
- If a model fails to load, try a different quantization option or check if the model is compatible with the current setup.

## Contributing

Contributions to MyLLM are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

[Add your chosen license here]
