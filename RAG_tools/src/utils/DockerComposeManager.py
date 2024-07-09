
import subprocess
import os
from dotenv import load_dotenv

class DockerComposeManager:
    def __init__(self, compose_file_path):
        self.compose_file_path = os.path.abspath(compose_file_path)
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(self.compose_file_path), '.env'))

    def run_command(self, command):
        try:
            result = subprocess.run(
                f"docker compose -f {self.compose_file_path} {command}",
                shell=True, check=True, capture_output=True, text=True
            )
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
            print(e.stderr)

    def start_containers(self):
        self.run_command("up -d")

    def stop_containers(self):
        self.run_command("down")

    def show_container_status(self):
        self.run_command("ps")
