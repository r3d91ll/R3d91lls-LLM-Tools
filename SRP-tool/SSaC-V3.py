import os
import requests
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
import hashlib
from collections import defaultdict
import logging
from pathlib import Path
import shutil
from markdownify import markdownify
from ratelimit import limits, sleep_and_retry
from collections import defaultdict
import openai
import json
import sys

# Constants
TIMEOUT = 10
CHUNK_SIZE = 8192

client = openai(api_key=os.environ["OPENAI_API_KEY"], organization=os.environ["ORGANIZATION_ID"])

class URLValidator:
    def __init__(self, allowed_domains):
        self.allowed_domains = allowed_domains

    def is_allowed_url(self, url):
        parsed_url = urlparse(url)
        return any(parsed_url.netloc == domain.split('/')[0] for domain in self.allowed_domains)

    def get_filename_from_url(self, url):
        return urlparse(url).path.split('/')[-1]

class ContentFetcher:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir
        os.makedirs(self.docs_dir, exist_ok=True)

    def _get_content_type(self, response):
        return response.headers.get('Content-Type', '')

    def fetch_url_content(self, url):
        try:
            response = requests.get(url, stream=True, timeout=TIMEOUT)
            if response.status_code != 200:
                logging.error(f"Non-success status code {response.status_code} while fetching {url}")
                return None
            
            content_type = self._get_content_type(response)
            if 'text/html' in content_type or 'application/xhtml+xml' in content_type:
                return self._save_content_as_html(url, response)
            else:
                return self._save_non_text_content(url, response)

        except requests.exceptions.RequestException as e:
            logging.error(f"Request exception occurred while fetching {url}: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred while fetching {url}: {e}")
            return None

    def _save_content_as_html(self, url, response):
        file_name = f'{self.get_filename_from_url(url)}.html'
        file_path = os.path.join(self.docs_dir, file_name)
        try:
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    file.write(chunk)
            logging.info(f"HTML file saved: {file_path}")
            return file_path
        except Exception as e:
            logging.error(f"An error occurred while saving HTML file {file_name}: {e}")
            return None

    def _save_non_text_content(self, url, response):
        file_name = self.get_filename_from_url(url)
        file_path = os.path.join(self.docs_dir, file_name)
        orig_file_path = os.path.join(self.docs_dir, 'orig_docs', file_name)
        try:
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    file.write(chunk)
            logging.info(f"File saved: {file_path}")
            shutil.copy(file_path, orig_file_path)
            return file_path
        except Exception as e:
            logging.error(f"An error occurred while saving non-text file {file_name}: {e}")
            return None

class WebScraper:
    def __init__(self, config):
        self.start_url = config.get("start_url")
        if not self.start_url or not self.url_validator.is_allowed_url(self.start_url):
            raise ValueError("Invalid or no start URL provided")

        self.url_validator = URLValidator(self.allowed_domains)
        self.content_fetcher = ContentFetcher(self.docs_dir)

    def _normalize_and_check_url(self, url):
        url, _ = urldefrag(url)
        return url if url not in self.visited_urls and self.url_validator.is_allowed_url(url) else None

    def scrape_page(self, url):
        normalized_url = self._normalize_and_check_url(url)
        if not normalized_url:
            return []
        self.visited_urls.add(normalized_url)
        logging.info(f"Scraping {normalized_url}...")
        content = self.content_fetcher.fetch_url_content(normalized_url)
        if content is None:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a', href=True)
        return [
            urljoin(normalized_url, link['href'])
            for link in links
            if self.url_validator.is_allowed_url(urljoin(normalized_url, link['href']))
        ]

from pathlib import Path
import openai
from markdownify import markdownify

class SPRGenerator:
    def __init__(self, client, assistant_id):
        self.client = client
        self.assistant_id = assistant_id

    def generate_spr(self, content):
        response = openai.Completion.create(
            engine="asst_oKlrkMCViaRtcLnFewRQJFUs",
            prompt=content,
            max_tokens=4096  # Adjust as needed
        )
        return response.choices[0].text

class MarkdownConverter:
    def convert_html_to_markdown(self, html_content):
        return markdownify(html_content)

class ContentProcessor:
    def __init__(self, base_directory, client, assistant_id):
        if not isinstance(base_directory, str):
            raise TypeError("base_directory must be a string")
        self.base_directory = base_directory
        self.directory = Path(base_directory)
        self.spr_generator = SPRGenerator(client, assistant_id)
        self.markdown_converter = MarkdownConverter()

    def create_directories(self):
        # Create directories for SRP_files, MD_files, HTML_files
        for subdir in ['SRP_files', 'MD_files', 'HTML_files']:
            Path(self.base_directory, subdir).mkdir(parents=True, exist_ok=True)

    def convert_html_to_markdown(self, file_path):
        # Convert HTML to Markdown
        with open(file_path, 'r') as file:
            html_content = file.read()
        markdown_content = self.markdown_converter.convert_html_to_markdown(html_content)
        # Call generate_and_save_spr with markdown_content
        self.generate_and_save_spr(file_path, markdown_content)

    def generate_and_save_spr(self, file_path, markdown_content):
        # Generate SPR using the OpenAI assistant
        spr_content = self.spr_generator.generate_spr(markdown_content)

        # Save SPR content
        spr_file_path = file_path.with_suffix('.spr')
        with open(spr_file_path, 'w') as file:
            file.write(spr_content)

    def process_directory(self):
        # Process all text and markdown files in the directory
        for file_path in self.directory.glob('*.txt'):
            self.clean_file(file_path)

        for file_path in self.directory.glob('*.md'):
            self.clean_file(file_path)

class DuplicateFileFinder:
    @staticmethod
    def handle_duplicates(directory):
        duplicates = DuplicateFileFinder.find_duplicates(directory)
        for file_hash, files in duplicates.items():
            if len(files) > 1:
                logging.warning(f"Duplicate files found: {', '.join(files)}")
                oldest_file = min(files, key=lambda f: os.path.getmtime(Path(directory, f)))
                files.remove(oldest_file)
                for file in files:
                    os.remove(Path(directory, file))

    @staticmethod
    def find_duplicates(directory):
        hashes = defaultdict(list)
        for filename in os.listdir(directory):
            file_path = Path(directory, filename)
            if file_path.is_file():
                file_hash = DuplicateFileFinder.compute_hash(file_path)
                hashes[file_hash].append(filename)
        return hashes

class MarkdownCleaner:
    def __init__(self, directory, text_regex_patterns=None, markdown_regex_patterns=None):
        self.directory = Path(directory)
        self.orig_directory = self.directory / 'orig_docs'
        self.orig_directory.mkdir(exist_ok=True)
        self.text_combined_pattern = self.load_regex_patterns(text_regex_patterns)
        self.markdown_combined_pattern = self.load_regex_patterns(markdown_regex_patterns)

    def load_regex_patterns(self, regex_patterns):
        if not isinstance(regex_patterns, list):
            logging.warning("Provided regex_patterns is not a list")
            return None

        try:
            combined_pattern = '|'.join(regex_patterns)
            return re.compile(combined_pattern, flags=re.UNICODE)
        except re.error as e:
            logging.error(f"Invalid regex pattern: {e}")
            return None

    def clean_file(self, original_file_path):
        content = original_file_path.read_text(encoding='utf-8')

        if self.text_combined_pattern and original_file_path.suffix == '.txt':
            cleaned_content = self.text_combined_pattern.sub('', content)
            logging.info(f"Cleaning text file: {original_file_path.name}")

            cleaned_file_path = self.directory / f'clean_{original_file_path.name}'
            with open(cleaned_file_path, 'w') as file:
                file.write(cleaned_content)

            logging.info(f"Cleaned file saved as: {cleaned_file_path.name}")
        elif self.markdown_combined_pattern and original_file_path.suffix == '.md':
            cleaned_content = self.markdown_combined_pattern.sub('', content)
            logging.info(f"Cleaning markdown file: {original_file_path.name}")

            cleaned_file_path = self.directory / f'clean_{original_file_path.name}'
            with open(cleaned_file_path, 'w') as file:
                file.write(cleaned_content)

            logging.info(f"Cleaned file saved as: {cleaned_file_path.name}")
        else:
            logging.warning(f"No regex pattern applied for {original_file_path.name}")

        original_file_path.rename(self.orig_directory / original_file_path.name)

    def process_directory(self):
        # Process all text and markdown files in the directory
        for file_path in self.directory.glob('*.txt'):
            self.clean_file(file_path)

        for file_path in self.directory.glob('*.md'):
            self.clean_file(file_path)

def main(config_file):
    # Read configuration from config.json
    try:
        with open(config_file, "r") as file:
            config = json.load(file)
    except FileNotFoundError:
        print(f"Configuration file {config_file} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the configuration file {config_file}.")
        sys.exit(1)

    # Initialize classes with configurations
    web_scraper_config = config.get("web_scraper", {})
    content_processor_config = config.get("content_processor", {})
    markdown_cleaner_config = config.get("markdown_cleaner", {})

    # Example of initializing a class with its config
    url_validator = URLValidator(web_scraper_config.get("allowed_domains"))
    web_scraper = WebScraper(web_scraper_config, url_validator)
    content_processor = ContentProcessor(
        content_processor_config.get("base_directory"),
        client,  # Assuming client is already initialized
        content_processor_config["spr_settings"]["assistant_id"]
    )

    # Add logic to use these objects as per your script's functionality
    # ...

if __name__ == "__main__":
    # Pass the path to the config file as an argument, or default to 'config.json'
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    main(config_path)
