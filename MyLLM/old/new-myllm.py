import os
import logging
from typing import Dict, List, Any, Optional, Generator
import yaml
import hashlib
import ast
import subprocess
import json
import time
from datetime import datetime
from functools import wraps

from sqlalchemy import create_engine, Column, String, Integer, MetaData, Table, Float, DateTime
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector

from langchain.embeddings import CodeBERTEmbeddings
from langchain_community.vectorstores import FAISS

import redis
from redis.exceptions import RedisError

# Enhanced Logging setup
def setup_logging(config):
    logging.basicConfig(level=config['logging']['level'],
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        filename=config['logging']['file'])
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    return logging.getLogger(__name__)

# Configuration validation
def validate_config(config: Dict[str, Any]) -> None:
    required_keys = ['embedding', 'paths', 'file_patterns', 'processing', 'indexing', 'logging', 'redis', 'database']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")
    
    if 'max_workers' not in config['processing']:
        raise ValueError("Missing 'max_workers' in processing configuration")
    if 'last_indexed_time' not in config['indexing']:
        raise ValueError("Missing 'last_indexed_time' in indexing configuration")
    if 'url' not in config['database']:
        raise ValueError("Missing 'url' in database configuration")

# Load YAML configuration
def load_yaml_config(config_path: str) -> Dict[str, Any]:
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        validate_config(config)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML configuration: {e}")

# Configuration
try:
    config = load_yaml_config('config.yaml')
    logger = setup_logging(config)
except (FileNotFoundError, ValueError) as e:
    print(f"Error loading configuration: {e}")
    exit(1)

def retry_on_exception(max_retries: int = 3, delay: int = 1, backoff: float = 1.5, exceptions: tuple = (Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = max_retries
            current_delay = delay
            while retries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.error(f"Error in {func.__name__}: {e}. Retries left: {retries}")
                    retries -= 1
                    if retries == 0:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator

class CacheManager:
    def __init__(self):
        self.connect_redis()

    @retry_on_exception(max_retries=5, delay=2, exceptions=(RedisError,))
    def connect_redis(self):
        self.redis_client = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port']
        )
        self.redis_client.ping()  # Test connection

    def is_cached(self, content_hash: str) -> bool:
        try:
            return self.redis_client.exists(content_hash)
        except RedisError as e:
            logger.error(f"Redis error in is_cached: {e}")
            return False

    def cache_embeddings(self, content_hash: str, embeddings: List[Dict[str, Any]]) -> None:
        try:
            self.redis_client.set(content_hash, json.dumps(embeddings))
        except RedisError as e:
            logger.error(f"Redis error in cache_embeddings: {e}")

    def get_cached_embeddings(self, content_hash: str) -> Optional[List[Dict[str, Any]]]:
        try:
            cached = self.redis_client.get(content_hash)
            return json.loads(cached) if cached else None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error retrieving cached embeddings: {e}")
            return None

class StreamFileManager:
    def __init__(self, directory):
        self.directory = directory

    def stream_files(self) -> Generator[Dict[str, Any], None, None]:
        for root, _, filenames in os.walk(self.directory):
            for filename in filenames:
                if filename.endswith('.py'):
                    file_path = os.path.join(root, filename)
                    yield {
                        'file_path': file_path,
                        'content': self.read_file(file_path)
                    }

    def read_file(self, file_path: str) -> str:
        with open(file_path, 'r') as f:
            return f.read()

class StreamCodeProcessor:
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.cache_manager = CacheManager()

    def process_stream(self, file_stream: Generator[Dict[str, Any], None, None]) -> Generator[Dict[str, Any], None, None]:
        for file_data in file_stream:
            file_path = file_data['file_path']
            content = file_data['content']

            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            cached_embeddings = self.cache_manager.get_cached_embeddings(content_hash)
            if cached_embeddings:
                logger.info(f"Using cached embeddings for {file_path}")
                yield {
                    'file_path': file_path,
                    'embeddings': cached_embeddings
                }
                continue

            embeddings = []
            commit_hash = self.get_git_commit_hash(file_path)

            # File-level embedding
            file_embedding = self.embedding_model.embed_documents([content])[0]
            embeddings.append({
                'embedding': file_embedding,
                'metadata': {
                    'file': file_path,
                    'layer': 'file',
                    'hash': content_hash,
                    'commit_hash': commit_hash
                }
            })

            # Class and function-level embeddings
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        self.process_class(node, content, file_path, content_hash, commit_hash, embeddings)
                    elif isinstance(node, ast.FunctionDef) and node.parent_field == 'body':
                        self.process_function(node, content, file_path, content_hash, commit_hash, embeddings)
            except SyntaxError as e:
                logger.error(f"Syntax error in file {file_path}: {e}")

            self.cache_manager.cache_embeddings(content_hash, embeddings)
            yield {
                'file_path': file_path,
                'embeddings': embeddings
            }

    def process_class(self, node, code_content, file_path, content_hash, commit_hash, embeddings):
        class_content = ast.get_source_segment(code_content, node)
        class_embedding = self.embedding_model.embed_documents([class_content])[0]
        embeddings.append({
            'embedding': class_embedding,
            'metadata': {
                'file': file_path,
                'layer': 'class',
                'class': node.name,
                'hash': content_hash,
                'commit_hash': commit_hash
            }
        })

    def process_function(self, node, code_content, file_path, content_hash, commit_hash, embeddings, class_name=None):
        func_content = ast.get_source_segment(code_content, node)
        func_embedding = self.embedding_model.embed_documents([func_content])[0]
        metadata = {
            'file': file_path,
            'layer': 'function',
            'function': node.name,
            'hash': content_hash,
            'commit_hash': commit_hash
        }
        if class_name:
            metadata['class'] = class_name
        embeddings.append({
            'embedding': func_embedding,
            'metadata': metadata
        })

    @staticmethod
    @retry_on_exception(max_retries=3, delay=1, exceptions=(subprocess.CalledProcessError,))
    def get_git_commit_hash(file_path: str) -> Optional[str]:
        try:
            return subprocess.check_output(["git", "log", "-n", "1", "--pretty=format:%H", file_path]).decode("utf-8")
        except subprocess.CalledProcessError:
            logger.warning(f"Failed to get git commit hash for {file_path}")
            return None

class StreamDatabaseManager:
    def __init__(self):
        self.metadata = MetaData()
        self.vector_table = Table(
            'vector_store', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('file', String),
            Column('layer', String),
            Column('class', String, nullable=True),
            Column('function', String, nullable=True),
            Column('hash', String),
            Column('commit_hash', String),
            Column('embedding', Vector(dim=config['embedding']['dimensions']))
        )
        self.metadata_table = Table(
            'file_metadata', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('file', String, unique=True),
            Column('file_size', Integer),
            Column('last_modified', DateTime),
            Column('author', String, nullable=True),
            Column('commit_hash', String)
        )
        self.engine = create_engine(config['database']['url'])
        self.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def store_stream(self, embedding_stream: Generator[Dict[str, Any], None, None]):
        session = self.Session()
        try:
            for embedding_data in embedding_stream:
                for embedding_dict in embedding_data['embeddings']:
                    vector_store = {
                        'file': embedding_dict['metadata']['file'],
                        'layer': embedding_dict['metadata']['layer'],
                        'class': embedding_dict['metadata'].get('class'),
                        'function': embedding_dict['metadata'].get('function'),
                        'hash': embedding_dict['metadata']['hash'],
                        'commit_hash': embedding_dict['metadata']['commit_hash'],
                        'embedding': embedding_dict['embedding']
                    }
                    session.execute(self.vector_table.insert().values(vector_store))
                session.commit()
        except Exception as e:
            logger.error(f"Error storing embeddings: {e}")
            session.rollback()
            raise
        finally:
            session.close()

def main():
    directory = config['paths']['codebase']
    embedding_model = CodeBERTEmbeddings(
        model_name=config['embedding']['model_name'],
        model_kwargs={"device": config['embedding']['device']}
    )

    file_manager = StreamFileManager(directory)
    code_processor = StreamCodeProcessor(embedding_model)
    db_manager = StreamDatabaseManager()

    file_stream = file_manager.stream_files()
    embedding_stream = code_processor.process_stream(file_stream)
    db_manager.store_stream(embedding_stream)

if __name__ == "__main__":
    main()
