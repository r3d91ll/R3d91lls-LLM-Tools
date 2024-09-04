import argparse
import os
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
from huggingface_hub import login
import logging
import colorama
import yaml
from typing import Tuple, Optional

def load_config(config_path='config.yaml'):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Set the API token as an environment variable
    if 'huggingface' in config and 'api_token' in config['huggingface']:
        os.environ['HF_API_TOKEN'] = config['huggingface']['api_token']
    else:
        print("Warning: HF_API_TOKEN not found in config file")
    
    return config

config = load_config()

colorama.init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'WARNING': colorama.Fore.YELLOW,
        'ERROR': colorama.Fore.RED,
        'CRITICAL': colorama.Fore.RED + colorama.Style.BRIGHT,
        'DEBUG': colorama.Fore.BLUE,
        'INFO': colorama.Fore.GREEN
    }

    def format(self, record):
        log_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, '')}{log_message}{colorama.Style.RESET_ALL}"

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(config['logging']['level'])
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter(config['logging']['format']))
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

MODELS_DIR = config['huggingface']['models_dir']

def check_models_directory():
    if not os.path.exists(MODELS_DIR):
        logger.error(f"Models directory does not exist: {MODELS_DIR}")
        return False
    if not os.access(MODELS_DIR, os.R_OK):
        logger.error(f"Cannot read from models directory: {MODELS_DIR}")
        return False
    logger.info(f"Models directory is accessible: {MODELS_DIR}")
    return True

def download_model(model_name):
    api_token = os.environ.get('HF_API_TOKEN')
    if not api_token:
        logger.error("HF_API_TOKEN is not set. Please check your config.yaml file.")
        return None, None

    try:
        logger.info("Authenticating with Hugging Face...")
        login(token=api_token)
        logger.info("Authentication successful.")
        
        model_path = os.path.join(MODELS_DIR, model_name.replace('/', '_'))
        
        logger.info(f"Attempting to download tokenizer for model: {model_name}...")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, token=api_token, trust_remote_code=True)
            tokenizer.save_pretrained(model_path)
            logger.info("Tokenizer downloaded successfully.")
        except Exception as e:
            logger.error(f"Error downloading tokenizer: {str(e)}")
            return None, None

        logger.info(f"Attempting to download model: {model_name}...")
        try:
            model = AutoModelForCausalLM.from_pretrained(model_name, token=api_token, trust_remote_code=True)
            model.save_pretrained(model_path)
            logger.info("Model downloaded successfully.")
        except Exception as e:
            logger.error(f"Error downloading model: {str(e)}")
            return None, None

        return tokenizer, model
    except Exception as e:
        logger.error(f"An error occurred while downloading the model: {str(e)}")
        return None, None
    
def list_models():
    models = [f for f in os.listdir(MODELS_DIR) if os.path.isdir(os.path.join(MODELS_DIR, f))]
    return models

def list_quantizations(model_name):
    model_path = os.path.join(MODELS_DIR, model_name)
    if not os.path.isdir(model_path):
        logger.error(f"Model directory not found: {model_path}")
        return []

    # List all items in the model directory
    items = os.listdir(model_path)

    # Filter for potential quantization files or directories
    quantizations = [
        item for item in items
        if os.path.isdir(os.path.join(model_path, item)) or  # Check if it's a directory
        item.endswith('.bin') or  # Check for .bin files (common for quantized models)
        item.endswith('.pt') or   # Check for .pt files (PyTorch format)
        item.endswith('.gguf')    # Check for .gguf files (used by some quantization formats)
    ]

    if not quantizations:
        logger.warning(f"No quantizations found for model: {model_name}")
        # If no quantizations found, we'll use the base model
        quantizations = ["base"]

    return quantizations

def load_model(model_name, quantization):
    model_path = os.path.join(MODELS_DIR, model_name, quantization)
    logger.info(f"Loading tokenizer and model from {model_path}...")
    
    try:
        # Load the model configuration
        model_config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
        
        # Determine the maximum sequence length
        if hasattr(model_config, 'max_position_embeddings'):
            max_length = model_config.max_position_embeddings
        else:
            max_length = config['model_defaults']['max_length']
            logger.warning(f"Could not determine max length for {model_name}. Using default: {max_length}")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(model_path, device_map='auto', torch_dtype=torch.float16, trust_remote_code=True)
        
        logger.info(f"Model loaded successfully. Max sequence length: {max_length}")
        
        return tokenizer, model, max_length
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {str(e)}")
        return None, None, config['model_defaults']['max_length']

def generate_response(model, tokenizer, prompt, max_length):
    logger.info("Generating response...")
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        inputs["input_ids"],
        max_length=min(max_length, config['model_defaults']['max_length']),
        num_return_sequences=1,
        num_beams=config['model_defaults']['num_beams'],
        early_stopping=config['model_defaults']['early_stopping']
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    logger.info("Response generation complete.")
    return response

def chat(model, tokenizer, max_length):
    print("Interactive chat session started. Type 'exit' to end the session.", flush=True)
    while True:
        prompt = input("You: ")
        if prompt.lower() == 'exit':
            print("Exiting chat session.", flush=True)
            break
        response = generate_response(model, tokenizer, prompt, max_length)
        print(f"Bot: {response}", flush=True)

def main():
    while True:
        print("\nMenu:", flush=True)
        print("1. Download a model", flush=True)
        print("2. Load a model", flush=True)
        print("3. Exit", flush=True)
        sys.stdout.flush()  # Ensure all output is flushed
        choice = input("Choose an option: ").strip()
        
        if not check_models_directory():
            print("Exiting due to issues with models directory.")
            sys.exit(1)
        
        if choice == '1':
            model_name = input("Enter the model name (e.g., mistralai/Codestral-22B-v0.1): ").strip()
            tokenizer, model = download_model(model_name)
            if tokenizer and model:
                logger.info(f"Model {model_name} downloaded and saved.")
            else:
                logger.error("Failed to download the model.")
        elif choice == '2':
            models = list_models()
            if not models:
                print("No models available. Please download a model first.", flush=True)
                continue
            print("\nAvailable models:", flush=True)
            for idx, model_name in enumerate(models, start=1):
                print(f"{idx}. {model_name}", flush=True)
            model_choice = int(input("Choose a model number to load: ").strip()) - 1
            if 0 <= model_choice < len(models):
                model_name = models[model_choice]
                quantizations = list_quantizations(model_name)  # You need to implement this function
                print("\nAvailable quantizations:", flush=True)
                for idx, quant in enumerate(quantizations, start=1):
                    print(f"{idx}. {quant}", flush=True)
                quant_choice = int(input("Choose a quantization: ").strip()) - 1
                if 0 <= quant_choice < len(quantizations):
                    quantization = quantizations[quant_choice]
                    tokenizer, model, max_length = load_model(model_name, quantization)
                    if tokenizer and model:
                        chat(model, tokenizer, max_length)
                    else:
                        print("Failed to load the model. Please try again.", flush=True)
                else:
                    print("Invalid quantization choice. Please try again.", flush=True)
            else:
                print("Invalid model choice. Please try again.", flush=True)

if __name__ == "__main__":
    main()
