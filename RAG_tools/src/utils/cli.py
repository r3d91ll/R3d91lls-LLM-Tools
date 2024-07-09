import typer
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.utils.config_utils import Config
from src.utils.ollama_manager import OllamaManager
from src.utils.DockerComposeManager import DockerComposeManager

app = typer.Typer()
config = Config()
ollama_manager = OllamaManager(config)
docker_manager = DockerComposeManager(str(project_root / "config" / "docker-compose.yml"))

@app.command()
def start():
    """Start the Ollama containers"""
    typer.echo("Starting Ollama containers...")
    docker_manager.start_containers()

@app.command()
def stop():
    """Stop the Ollama containers"""
    typer.echo("Stopping Ollama containers...")
    docker_manager.stop_containers()

@app.command()
def status():
    """Check the status of the Ollama containers"""
    typer.echo("Checking container status...")
    docker_manager.show_container_status()

@app.command()
def chat():
    """Start a chat session with the LLM"""
    typer.echo("Starting chat session. Type 'exit' to end the session.")
    logging.debug(f"Configuration values:")
    logging.debug(f"OLLAMA_LLM_CONTAINER_NAME: {config.OLLAMA_LLM_CONTAINER_NAME}")
    logging.debug(f"OLLAMA_LLM_PORT: {config.OLLAMA_LLM_PORT}")
    logging.debug(f"OLLAMA_LLM_MODEL: {config.OLLAMA_LLM_MODEL}")
    logging.debug(f"Using model: {ollama_manager.model}")
    logging.debug(f"Ollama port: {ollama_manager.port}")
    
    # Check if the model is running
    if not ollama_manager.is_model_running():
        typer.echo(f"Error: Model {ollama_manager.model} is not running. Please start the model first.")
        return

    while True:
        prompt = typer.prompt("You")
        if prompt.lower() == 'exit':
            break
        logging.debug(f"Sending prompt to OllamaManager: {prompt}")
        response = ollama_manager.generate_response(prompt)
        logging.debug(f"Received response from OllamaManager: {response[:100]}...")  # Log first 100 chars
        if response.startswith("Error:") or response.startswith("Unexpected error:"):
            typer.echo(f"LLM Error: {response}", err=True)
        else:
            typer.echo(f"LLM: {response}")

if __name__ == "__main__":
    app()
