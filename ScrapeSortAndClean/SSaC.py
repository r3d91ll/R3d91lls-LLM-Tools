import os
import requests
import html2text
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
import hashlib
from collections import defaultdict
import re
from pathlib import Path
import shutil
from markdownify import markdownify
import json
import sys
import argparse
import logging
from ratelimit import limits, sleep_and_retry
import pathlib

# Constants
TIMEOUT = 10
CHUNK_SIZE = 8192

class WebScraper:
    def __init__(self, config):
        self.start_url = config.get("start_url")
        self.allowed_domains = config.get("allowed_domains")
        self.docs_dir = config.get("docs_dir")
        if not os.path.exists(self.docs_dir):
            raise FileNotFoundError(f"The specified 'docs_dir' does not exist: {self.docs_dir}")
        os.makedirs(self.docs_dir, exist_ok=True)   # Create working directory if it doesn't exist

    def is_allowed_url(self, url):
        parsed_url = urlparse(url)
        return any(parsed_url.netloc == domain.split('/')[0] for domain in self.allowed_domains)

    def get_filename_from_url(self, url):
        return urlparse(url).path.split('/')[-1]

    @sleep_and_retry
    @limits(calls=1, period=1)
    def fetch_url_content(self, url):
        try:
            response = requests.get(url, stream=True, timeout=TIMEOUT)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')

            if 'text/html' in content_type or 'application/xhtml+xml' in content_type:
                return self._save_content_as_html(url, response)
            else:
                # Handle non-HTML content
                return self._save_non_text_content(url, response)
        except Exception as e:
            logging.error(f"An error occurred while fetching {url}: {e}")
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
        os.makedirs(os.path.join(self.docs_dir, 'orig_docs'), exist_ok=True)
        orig_file_path = os.path.join(self.docs_dir, 'orig_docs', file_name)
        try:
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    file.write(chunk)
            logging.info(f"File saved: {file_path}")
            logging.info(f"File written successfully: {file_path}")
            # Copy the file to the orig_docs directory only if it's not a text file
            if not self._is_text_file(file_name):
                shutil.copy(file_path, orig_file_path)
            return file_path
        except Exception as e:
            logging.error(f"An error occurred while saving non-text file {file_name}: {e}")
            return None

    def _is_text_file(self, file_name):
        # Recognized text file extensions
        text_file_extensions = ['.json', '.html', '.yaml', '.sh', '.ps1', '.py']
        return any(file_name.endswith(ext) for ext in text_file_extensions)

    def scrape_page(self, url, visited_urls):
        url, _ = urldefrag(url)
        if url in visited_urls or not self.is_allowed_url(url):
            return []
        visited_urls.add(url)
        logging.info(f"Scraping {url}...")
        content = self.fetch_url_content(url)
        if content is None:
            return []

        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a', href=True)
        scraped_urls = []
        for link in links:
            absolute_url = urljoin(url, link['href'])
            if self.is_allowed_url(absolute_url):
                scraped_urls.append(absolute_url)
        return scraped_urls

class ContentProcessor:
    def __init__(self, docs_dir, config, convert_to_markdown):
        self.docs_dir = docs_dir 
        self.config = config
        self.docs_dir = pathlib.Path(self.config["docs_dir"])
        self.convert_to_markdown = convert_to_markdown
        
        docs_dir = pathlib.Path(self.config["docs_dir"])

    def process_directory(self):
        """
        Process all HTML files in the directory.
        Converts HTML files to Markdown and processes text files.
        """
        for file_path in self.docs_dir.iterdir():
            if file_path.suffix == '.html':
                # Convert HTML to Markdown
                self.convert_html_to_markdown(file_path)
            elif file_path.suffix == '.txt' and not self.convert_to_markdown:
                # Process text files if not converting to Markdown
                self.convert_html_to_text(file_path)

    def convert_html_to_markdown(self, file_path):

        try:
            with open(file_path, 'r') as f:
                html_content = f.read()
            # Convert HTML to Markdown 
            markdown_content = self.html_to_markdown(html_content)
            # Write markdown content to file  
            markdown_file_path = file_path.with_suffix('.md')
            with open(markdown_file_path, 'w') as f:
                f.write(markdown_content)
            logging.info(f"Markdown file written to {markdown_file_path}")
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")

    def convert_html_to_text(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            text_content = self.html_to_text(html_content)

            # Save the converted content as a text file
            text_file_path = file_path.with_suffix('.txt')
            with open(text_file_path, 'w', encoding='utf-8') as file:
                file.write(text_content)
                logging.info(f"Text file written successfully: {text_file_path}")
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")

    def html_to_markdown(self, html_content):
        return markdownify(html_content)

    def html_to_text(self, html_content):
        return html2text.html2text(html_content)

class DuplicateFileFinder:
    @staticmethod
    def compute_sha256(file_path):
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as file:
            hasher.update(file.read())
        return hasher.hexdigest()

    @staticmethod
    def handle_duplicates(directory):
        duplicates = DuplicateFileFinder.find_duplicates(directory)
        for file_hash, files in duplicates.items():
            if len(files) > 1:
                logging.warning(f"Duplicate files found: {', '.join(files)}")
                oldest_file = min(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
                files.remove(oldest_file)
                for file in files:
                    os.remove(os.path.join(directory, file))

    @staticmethod
    def find_duplicates(directory):
        hashes = defaultdict(list)
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_hash = DuplicateFileFinder.compute_sha256(file_path)
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
        if regex_patterns and isinstance(regex_patterns, list):
            combined_pattern = '|'.join(regex_patterns)
            return re.compile(combined_pattern, flags=re.UNICODE)
        else:
            logging.warning("Invalid regex patterns provided.")
            return None

    def clean_file(self, original_file_path):
        content = original_file_path.read_text(encoding='utf-8')

        if self.text_combined_pattern and original_file_path.suffix == '.txt':
            cleaned_content = self.text_combined_pattern.sub('', content)
            logging.info(f"Cleaning text file: {original_file_path.name}")

            cleaned_file_name = f'clean_{original_file_path.name}'
            new_file_path = self.directory / cleaned_file_name
            new_file_path.write_text(cleaned_content, encoding='utf-8')

            logging.info(f"Cleaned file saved as: {cleaned_file_name}")
        elif self.markdown_combined_pattern and original_file_path.suffix == '.md':
            cleaned_content = self.markdown_combined_pattern.sub('', content)
            logging.info(f"Cleaning markdown file: {original_file_path.name}")

            cleaned_file_name = f'clean_{original_file_path.name}'
            new_file_path = self.directory / cleaned_file_name
            new_file_path.write_text(cleaned_content, encoding='utf-8')

            logging.info(f"Cleaned file saved as: {cleaned_file_name}")
        else:
            logging.warning(f"No regex pattern applied for {original_file_path}")

        original_file_path.rename(self.orig_directory / original_file_path.name)


    def process_directory(self):
        # Process all text and markdown files in the directory
        text_files = list(self.directory.glob('*.txt'))
        markdown_files = list(self.directory.glob('*.md'))

        for file_path in text_files + markdown_files:
            self.clean_file(file_path)

def main(config_file):
    with open(config_file) as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error loading JSON configuration: {e}")
            return
    
    # Log the loaded configuration for debugging
    logging.info(f"Configuration loaded: {config}")
    os.makedirs(config["docs_dir"], exist_ok=True)

    scraper = WebScraper(config)
    content_processor = ContentProcessor(config["docs_dir"], config, convert_to_markdown=True) 

    visited_urls = set()
    urls_to_scrape = [config["start_url"]]

    while urls_to_scrape:
        url = urls_to_scrape.pop(0)
        scraped_urls = scraper.scrape_page(url, visited_urls)
        urls_to_scrape.extend(scraped_urls)

    DuplicateFileFinder.handle_duplicates(config["docs_dir"])

    content_processor = ContentProcessor(config["docs_dir"], config, convert_to_markdown=True) 
    content_processor.process_directory()

    """ 
    if "regex_pattern" in config:
        cleaner = MarkdownCleaner(config["docs_dir"], markdown_regex_patterns=config["regex_pattern"])
        cleaner.process_directory()
    else:
        logging.info("Skipping the cleaning process.")
    """

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape, sort, and clean HTML files.")
    parser.add_argument("config_file", help="Path to the JSON configuration file")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.config_file)
