import os
import requests
import markdownify
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
import json
import argparse
import logging
from ratelimit import limits, sleep_and_retry
from pathlib import Path
import time
from datetime import datetime, timedelta

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

    def is_file_recent(self, file_path):
            """Check if the file at file_path is less than 24 hours old."""
            if not os.path.exists(file_path):
                return False
            file_creation_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            return datetime.now() - file_creation_time < timedelta(days=1)

    @sleep_and_retry
    @limits(calls=1, period=1)
    def fetch_url_content(self, url):
        file_name = f'{self.get_filename_from_url(url)}.html'
        file_path = os.path.join(self.docs_dir, file_name)

        if self.is_file_recent(file_path):
            logging.info(f"Recent file already exists, skipping download: {file_name}")
            return None  # Or return some indicator that file was not downloaded
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
        file_path = self.fetch_url_content(url)
        if file_path is None:
            return []

        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')

        links = soup.find_all('a', href=True)
        scraped_urls = []
        for link in links:
            absolute_url = urljoin(url, link['href'])
            if self.is_allowed_url(absolute_url):
                scraped_urls.append(absolute_url)
        return scraped_urls

class HTMLToMarkdownConverter:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def html_to_markdown(self, html_content):
        # Use HTMLToMarkdownConverter here
        converter = HTMLToMarkdownConverter(heading_style="ATX")
        return converter.convert(html_content)

    def process_directory(self):
        consolidated_md_path = os.path.join(self.docs_dir, 'consolidated.md')
        with open(consolidated_md_path, 'w', encoding='utf-8') as consolidated_file:
            for html_file_path in Path(self.docs_dir).glob('*.html'):
                with open(html_file_path, 'r', encoding='utf-8') as html_file:
                    html_content = html_file.read()
                    markdown_content = self.html_to_markdown(html_content)
                    consolidated_file.write(markdown_content + "\n\n")
                os.remove(html_file_path)
        logging.info(f"Consolidated Markdown file created: {consolidated_md_path}")

def main(config_file):
    with open(config_file) as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error loading JSON configuration: {e}")
            return
    
    logging.info(f"Configuration loaded: {config}")
    os.makedirs(config["docs_dir"], exist_ok=True)

    scraper = WebScraper(config)

    visited_urls = set()
    urls_to_scrape = [config["start_url"]]

    while urls_to_scrape:
        url = urls_to_scrape.pop(0)
        scraped_urls = scraper.scrape_page(url, visited_urls)
        urls_to_scrape.extend(scraped_urls)

    converter = HTMLToMarkdownConverter(config["docs_dir"])
    converter.process_directory()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web scraping script.")
    parser.add_argument("config_file", help="Path to the JSON configuration file")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.config_file)
