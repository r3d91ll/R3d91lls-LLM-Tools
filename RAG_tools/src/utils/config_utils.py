
import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
        # Database configurations
        self.POSTGRES_DB = os.getenv('POSTGRES_DB')
        self.POSTGRES_USER = os.getenv('POSTGRES_USER')
        self.POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
        self.POSTGRES_HOST = os.getenv('POSTGRES_HOST')
        self.POSTGRES_PORT = os.getenv('POSTGRES_PORT')
        
        self.NEO4J_AUTH = os.getenv('NEO4J_AUTH')
        self.NEO4J_HOST = os.getenv('NEO4J_HOST')
        self.NEO4J_HTTP_PORT = os.getenv('NEO4J_HTTP_PORT')
        self.NEO4J_BOLT_PORT = os.getenv('NEO4J_BOLT_PORT')
        
        # pgAdmin configurations
        self.PGADMIN_PORT = os.getenv('PGADMIN_PORT')
        self.PGADMIN_DEFAULT_EMAIL = os.getenv('PGADMIN_DEFAULT_EMAIL')
        self.PGADMIN_DEFAULT_PASSWORD = os.getenv('PGADMIN_DEFAULT_PASSWORD')
        
        # Docker configurations
        self.POSTGRES_CONTAINER_NAME = os.getenv('POSTGRES_CONTAINER_NAME')
        self.NEO4J_CONTAINER_NAME = os.getenv('NEO4J_CONTAINER_NAME')
        self.PGADMIN_CONTAINER_NAME = os.getenv('PGADMIN_CONTAINER_NAME')
        self.DOCKER_NETWORK_NAME = os.getenv('DOCKER_NETWORK_NAME')

        # Ollama configurations
        self.OLLAMA_EMBEDDING_CONTAINER_NAME = os.getenv('OLLAMA_EMBEDDING_CONTAINER_NAME')
        self.OLLAMA_EMBEDDING_PORT = int(os.getenv('OLLAMA_EMBEDDING_PORT', 11434))
        self.OLLAMA_EMBEDDING_MODEL = os.getenv('OLLAMA_EMBEDDING_MODEL')
        self.OLLAMA_EMBEDDING_GPU = int(os.getenv('OLLAMA_EMBEDDING_GPU', 0))
        self.OLLAMA_LLM_CONTAINER_NAME = os.getenv('OLLAMA_LLM_CONTAINER_NAME')
        self.OLLAMA_LLM_PORT = int(os.getenv('OLLAMA_LLM_PORT', 11435))
        self.OLLAMA_LLM_MODEL = os.getenv('OLLAMA_LLM_MODEL')
        self.OLLAMA_LLM_GPU = int(os.getenv('OLLAMA_LLM_GPU', 1))
        self.OLLAMA_MODELS_PATH = os.getenv('OLLAMA_MODELS_PATH')
        self.OLLAMA_LLM_PATH = os.getenv('OLLAMA_LLM_PATH')

    def get_postgres_connection_params(self):
        return {
            "dbname": self.POSTGRES_DB,
            "user": self.POSTGRES_USER,
            "password": self.POSTGRES_PASSWORD,
            "host": self.POSTGRES_HOST,
            "port": self.POSTGRES_PORT
        }

    def print_all_attributes(self):
        print("All Config attributes:")
        for attr, value in self.__dict__.items():
            print(f"{attr}: {value}")

    def get_neo4j_connection_params(self):
        return {
            "uri": f"bolt://{self.NEO4J_HOST}:{self.NEO4J_BOLT_PORT}",
            "auth": tuple(self.NEO4J_AUTH.split('/'))
        }
