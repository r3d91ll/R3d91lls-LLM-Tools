import os
import requests
import html2text
import subprocess
import argparse
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup

def get_file_name(url, is_notebook=False):
    path = urlparse(url).path
    if is_notebook:
        return os.path.basename(path)
    page_name = os.path.splitext(os.path.basename(path))[0]
    return f"{page_name}.md"

def is_allowed_url(url, allowed_domains):
    parsed_url = urlparse(url)
    for domain in allowed_domains:
        domain_parts = domain.split('/')
        if parsed_url.netloc == domain_parts[0] and (len(domain_parts) == 1 or parsed_url.path.startswith('/' + '/'.join(domain_parts[1:]))):
            return True
    return False

def convert_notebook_to_markdown(notebook_path):
    markdown_path = f'{os.path.splitext(notebook_path)[0]}.md'
    try:
        subprocess.run(["jupyter", "nbconvert", "--to", "markdown", notebook_path], check=True)
        print(f"Converted {notebook_path} to Markdown: {markdown_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting {notebook_path} to Markdown: {e}")

def scrape_page(url, allowed_domains, visited_urls, docs_dir):
    url, _ = urldefrag(url)
    if not is_allowed_url(url, allowed_domains) or url in visited_urls:
        return []

    print(f"Scraping {url}...")
    visited_urls.add(url)

    try:
        response = requests.get(url)
        content = response.content

        if url.endswith('.ipynb'):
            filepath = os.path.join(docs_dir, get_file_name(url, is_notebook=True))
            with open(filepath, 'wb') as file:
                file.write(content)
                print(f"Saved notebook: {filepath}")
            convert_notebook_to_markdown(filepath)
        else:
            soup = BeautifulSoup(content, 'html.parser')
            text_maker = html2text.HTML2Text()
            text_maker.ignore_links = False
            markdown = text_maker.handle(soup.prettify())

            filepath = os.path.join(docs_dir, get_file_name(url))
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(markdown)
                print(f"Saved HTML as Markdown: {filepath}")

        soup = BeautifulSoup(content, 'html.parser')
        return [urljoin(url, link['href']) for link in soup.findAll('a', href=True)]

    except Exception as e:
        print(f"An error occurred while scraping {url}: {e}")

    return []

def scrape_pages(start_url, allowed_domains, docs_dir):
    visited_urls = set()
    pages_to_visit = [start_url]

    while pages_to_visit:
        current_url = pages_to_visit.pop()
        pages_to_visit.extend(
            link
            for link in scrape_page(current_url, allowed_domains, visited_urls, docs_dir)
            if link not in visited_urls
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Scraper for Jupyter Notebooks and HTML pages")
    parser.add_argument("start_url", help="The starting URL for the scraper")
    parser.add_argument("allowed_domains", help="Comma-separated list of allowed domains")
    parser.add_argument("docs_dir", help="Directory to save the documents")

    args = parser.parse_args()

    START_URL = args.start_url
    ALLOWED_DOMAINS = args.allowed_domains.split(',')
    DOCS_DIR = args.docs_dir

    os.makedirs(DOCS_DIR, exist_ok=True)
    scrape_pages(START_URL, ALLOWED_DOMAINS, DOCS_DIR)
