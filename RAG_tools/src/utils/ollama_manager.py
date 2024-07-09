import os
import requests
import time
import logging
import json
from .DockerComposeManager import DockerComposeManager
from .config_utils import Config

class OllamaManager:
    def __init__(self, config: Config):
        self.config = config
        self.container_name = self.config.OLLAMA_LLM_CONTAINER_NAME
        self.port = self.config.OLLAMA_LLM_PORT
        self.model = self.config.OLLAMA_LLM_MODEL
        self.gpu = self.config.OLLAMA_LLM_GPU
        
        self.models_path = self.config.OLLAMA_MODELS_PATH or os.path.expanduser('~/ollama_models')
        self.llm_path = self.config.OLLAMA_LLM_PATH or os.path.join(self.models_path, 'llm')
        
        # Ensure directories exist
        os.makedirs(self.models_path, exist_ok=True)
        os.makedirs(self.llm_path, exist_ok=True)
        
        # Initialize DockerComposeManager
        docker_compose_path = os.path.join('..', 'config', 'docker-compose.yml')
        self.docker_manager = DockerComposeManager(docker_compose_path)

        logging.info(f"OllamaManager initialized with models_path: {self.models_path}, llm_path: {self.llm_path}")
        logging.info(f"Using model: {self.model} on port: {self.port}")

    def generate_response(self, prompt):
        try:
            payload = {
                'model': self.model,
                'prompt': prompt
            }
            logging.debug(f"Sending request to Ollama API with payload: {payload}")
            logging.debug(f"API URL: http://localhost:{self.port}/api/generate")
            
            response = requests.post(
                f'http://localhost:{self.port}/api/generate',
                json=payload,
                stream=True
            )
            logging.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        logging.debug(f"Received chunk: {chunk}")
                        if 'response' in chunk:
                            token = chunk['response']
                            full_response += token
                            print(token, end='', flush=True)
                        if chunk.get('done', False):
                            break
                    except json.JSONDecodeError:
                        logging.warning(f"Failed to decode JSON: {line}")
            
            print("\n")  # New line after the response
            return full_response.strip()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error generating response: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"Response content: {e.response.text}")
            return f"Error: {str(e)}"
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return f"Unexpected error: {str(e)}"

    def is_model_running(self):
        try:
            response = requests.get(f'http://localhost:{self.port}/api/tags')
            response.raise_for_status()
            models = response.json()
            logging.debug(f"Available models: {models}")
            return self.model in [model['name'] for model in models['models']]
        except requests.exceptions.RequestException as e:
            logging.error(f"Error checking if model is running: {e}")
            return False

    def pull_model(self):
        logging.debug(f"Starting pull_model for model: {self.model}")
        logging.debug(f"self.models_path: {self.models_path}")
        logging.debug(f"self.model: {self.model}")
        
        try:
            model_path = os.path.join(self.models_path, 'models', 'manifests', 'registry.ollama.ai', 'library', self.model)
            logging.info(f"Checking for model at path: {model_path}")
        except Exception as e:
            logging.error(f"Error constructing model path: {str(e)}")
            raise
        
        if os.path.exists(model_path):
            logging.info(f"Model {self.model} already exists. Skipping download.")
            return

        logging.info(f"Pulling model {self.model}...")
        try:
            response = requests.post(f'http://localhost:{self.port}/api/pull', json={'name': self.model}, stream=True)
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    print(line.decode())
        except requests.exceptions.RequestException as e:
            logging.error(f"Error pulling model: {str(e)}")
            raise

    def start_container(self):
        self.docker_manager.start_containers()
        logging.info(f"Started container: {self.container_name}")

    def stop_container(self):
        self.docker_manager.stop_containers()
        logging.info(f"Stopped container: {self.container_name}")

    def wait_for_ollama(self, max_attempts=5, delay=5):
        for attempt in range(max_attempts):
            try:
                response = requests.get(f'http://localhost:{self.port}/api/tags')
                if response.status_code == 200:
                    logging.info(f"Successfully connected to Ollama on port {self.port}")
                    return True
            except requests.exceptions.RequestException:
                logging.warning(f"Attempt {attempt + 1}/{max_attempts}: Ollama on port {self.port} is not ready yet. Retrying in {delay} seconds...")
                time.sleep(delay)
        logging.error(f"Failed to connect to Ollama after {max_attempts} attempts")
        return False
