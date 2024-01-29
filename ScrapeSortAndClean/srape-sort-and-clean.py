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

class WebScraper:
    def __init__(self, start_url, allowed_domains, docs_dir):
        self.start_url = start_url
        self.allowed_domains = allowed_domains
        self.docs_dir = docs_dir
        os.makedirs(docs_dir, exist_ok=True)  # Create working directory if it doesn't exist

    def is_allowed_url(self, url):
        parsed_url = urlparse(url)
        return any(parsed_url.netloc == domain.split('/')[0] for domain in self.allowed_domains)

    def get_filename_from_url(self, url):
        return urlparse(url).path.split('/')[-1]

    def fetch_url_content(self, url):
        try:
            response = requests.get(url, stream=True)  # Use stream to handle large files
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')

            # Check if the content is text-based
            if 'text' in content_type or 'html' in content_type or 'json' in content_type:
                return response.text
            else:
                return self._extracted_from_fetch_url_content_11(url, response)
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching {url}: {e}")
            return None

    def _save_non_text_content(self, url, response):
        file_name = self.get_filename_from_url(url)
        file_path = os.path.join(self.docs_dir, file_name)
        orig_file_path = os.path.join(self.docs_dir, 'orig_docs', file_name)

        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        # Copy the file to the orig_docs directory only if it's not a text file
        if not self._is_text_file(file_name):
            shutil.copy(file_path, orig_file_path)

        return file_path

    def _is_text_file(self, file_name):
        # Recognized text file extensions
        text_file_extensions = ['.json', '.html', '.yaml', '.sh', '.ps1', '.py']
        return any(file_name.endswith(ext) for ext in text_file_extensions)

    def _extracted_from_fetch_url_content_11(self, url, response):
        file_name = self.get_filename_from_url(url)
        file_path = os.path.join(self.docs_dir, file_name)
        orig_file_path = os.path.join(self.docs_dir, 'orig_docs', file_name)

        with open(file_path, 'wb') as file, open(orig_file_path, 'wb') as orig_file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                orig_file.write(chunk)
        print(f"Downloaded non-text file: {file_name}")
        return None  # Return None to indicate no further processing needed

    def scrape_page(self, url, visited_urls):
        url, _ = urldefrag(url)
        if url in visited_urls or not self.is_allowed_url(url):
            return []
        visited_urls.add(url)
        print(f"Scraping {url}...")
        content = self.fetch_url_content(url)
        if content is None:
            return []
        soup = BeautifulSoup(content, 'html.parser')
        markdown = html2text.html2text(soup.prettify())
        filepath = os.path.join(self.docs_dir, urlparse(url).path.replace('/', '_') + '.md')
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(markdown)
        return [urljoin(url, link['href']) for link in soup.findAll('a', href=True)]

    def scrape_pages(self):
        visited_urls = set()
        pages_to_visit = [self.start_url]
        while pages_to_visit:
            current_url = pages_to_visit.pop()
            for link in self.scrape_page(current_url, visited_urls):
                if link not in visited_urls:
                    pages_to_visit.append(link)

class ContentProcessor:
    def __init__(self, docs_dir):
        self.docs_dir = Path(docs_dir)

    def process_directory(self):
        # Iterate through all files in the directory
        for file_path in self.docs_dir.iterdir():
            # Process only HTML files for now
            if file_path.suffix == '.html':
                self.convert_html_to_markdown(file_path)

    def convert_html_to_markdown(self, file_path):
        # TODO: Implement the logic to convert HTML to Markdown
        # Example placeholder implementation
        with open(file_path, 'r') as file:
            html_content = file.read()
        markdown_content = self.html_to_markdown(html_content)
        
        # Save the converted content as a Markdown file
        markdown_file_path = file_path.with_suffix('.md')
        with open(markdown_file_path, 'w') as file:
            file.write(markdown_content)

class DuplicateFileFinder:
    @staticmethod
    def compute_sha256(file_path):
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as file:
            hasher.update(file.read())
        return hasher.hexdigest()

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
    def __init__(self, directory, regex_file=None):
        self.directory = Path(directory)
        self.orig_directory = self.directory / 'orig_docs'
        self.orig_directory.mkdir(exist_ok=True)
        self.combined_pattern = self.load_regex_patterns(regex_file)

    def load_regex_patterns(self, regex_file):
        if regex_file and Path(regex_file).exists():
            patterns = Path(regex_file).read_text().splitlines()
            print("Loaded patterns:", patterns)  # Debugging print statement
            combined_pattern = '|'.join(patterns)
            print("Combined pattern:", combined_pattern)  # Debugging print statement
            return re.compile(combined_pattern, flags=re.UNICODE)
        else:
            print("Regex file not found or not provided.")  # Debugging print statement
            return None
        
    def clean_file(self, original_file_path):
        # sourcery skip: extract-method, use-fstring-for-concatenation
        content = original_file_path.read_text(encoding='utf-8')

        if self.combined_pattern:
            cleaned_content = self.combined_pattern.sub('', content)
            print(f"Cleaning file: {original_file_path.name}")

            cleaned_file_name = 'clean_' + original_file_path.name
            new_file_path = self.directory / cleaned_file_name
            new_file_path.write_text(cleaned_content, encoding='utf-8')

            print(f"Cleaned file saved as: {cleaned_file_name}")
        else:
            print(f"No regex pattern applied for {original_file_path}")

        original_file_path.rename(self.orig_directory / original_file_path.name)


    def process_directory(self):
        # Process all markdown files in the directory
        markdown_files = list(self.directory.glob('*.md'))
        for file_path in markdown_files:
            self.clean_file(file_path)

def main():
    start_url = input("Enter the start URL: ")
    allowed_domains = input("Enter allowed domains (comma-separated): ").split(',')
    docs_dir = input("Enter the directory to save documents: ")
    regex_file = input("Enter the path to the regex file (leave blank to skip cleaning): ")

    if regex_file.strip():
        # Create 'orig_docs' directory if regex file is provided
        orig_docs_dir = os.path.join(docs_dir, 'orig_docs')
        os.makedirs(orig_docs_dir, exist_ok=True)

    scraper = WebScraper(start_url, allowed_domains, docs_dir)
    scraper.scrape_pages()

    duplicates = DuplicateFileFinder.find_duplicates(docs_dir)
    for file_hash, files in duplicates.items():
        if len(files) > 1:
            print(f"Duplicate files found: {', '.join(files)}")
            keep = input("Enter the name of the file to keep (others will be deleted): ")
            for file in files:
                if file != keep:
                    os.remove(os.path.join(docs_dir, file))

    if regex_file.strip():
        cleaner = MarkdownCleaner(docs_dir, regex_file)
        cleaner.process_directory()
    else:
        print("Skipping the cleaning process.")

if __name__ == "__main__":
    main()
