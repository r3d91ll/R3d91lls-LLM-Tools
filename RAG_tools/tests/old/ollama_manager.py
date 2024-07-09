import time
import requests
import docker

class OllamaManager:
    def __init__(self, container_name, port, model, gpu=None, models_path='/root/.ollama'):
        # This is the constructor. It sets up the initial state of our OllamaManager.
        self.container_name = container_name  # A unique name for our Docker container
        self.port = port  # The network port Ollama will use to communicate
        self.model = model  # The AI model we want to use (like "tinyllama" or "gpt-2")
        self.gpu = gpu  # Whether to use a graphics card to speed things up (if available)
        self.models_path = models_path  # Where to store the AI models on our computer
        self.client = docker.from_env()  # This lets us talk to Docker

    def start_container(self):
        # This method starts our Ollama container
        try:
            # First, we check if the container already exists
            container = self.client.containers.get(self.container_name)
            if container.status != 'running':
                # If it exists but isn't running, we start it
                container.start()
                print(f"Started existing container: {self.container_name}")
            else:
                # If it's already running, we just let ourselves know
                print(f"Container {self.container_name} is already running.")
        except docker.errors.NotFound:
            # If the container doesn't exist, we create a new one
            volumes = {self.models_path: {'bind': '/root/.ollama', 'mode': 'rw'}}
            environment = {"OLLAMA_HOST": f"0.0.0.0:{self.port}"}
            device_requests = None
            if self.gpu is not None:
                # If we want to use a GPU, we set that up here
                device_requests = [docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]
            
            # Now we create and start the new container
            self.client.containers.run(
                'ollama/ollama',
                name=self.container_name,
                detach=True,
                ports={f'{self.port}/tcp': self.port},
                volumes=volumes,
                environment=environment,
                device_requests=device_requests
            )
            print(f"Created and started new container: {self.container_name}")

    def wait_for_ollama(self, max_attempts=5, delay=5):
        # This method checks if Ollama is ready to use
        for attempt in range(max_attempts):
            try:
                # We try to connect to Ollama
                response = requests.get(f'http://localhost:{self.port}/api/tags')
                if response.status_code == 200:
                    # If we get a good response, Ollama is ready!
                    print(f"Successfully connected to Ollama on port {self.port}")
                    return True
            except requests.exceptions.RequestException:
                # If we can't connect, we wait and try again
                print(f"Attempt {attempt + 1}/{max_attempts}: Ollama on port {self.port} is not ready yet. Retrying in {delay} seconds...")
                time.sleep(delay)
        return False

    def pull_model(self):
        # This method downloads the AI model we want to use
        response = requests.post(f'http://localhost:{self.port}/api/pull', json={'name': self.model})
        print(f"Pulling model {self.model}...")
        for line in response.iter_lines():
            print(line.decode())

    def generate_response(self, prompt):
        # This method asks the AI model a question and gets an answer
        response = requests.post(f'http://localhost:{self.port}/api/generate', json={'model': self.model, 'prompt': prompt})
        return response.json()['response']

    def stop_container(self):
        # This method stops our Ollama container
        try:
            container = self.client.containers.get(self.container_name)
            container.stop()
            print(f"Stopped container: {self.container_name}")
        except docker.errors.NotFound:
            print(f"Container {self.container_name} not found.")
