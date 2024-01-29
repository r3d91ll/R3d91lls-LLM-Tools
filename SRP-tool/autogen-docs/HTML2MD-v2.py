import re
import html2text
import os
import sys

def html_to_markdown(html_content):
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    return converter.handle(html_content)

def generate_anchor(header):
    # Convert a header to a Markdown-friendly anchor
    anchor = header.lower().strip()
    anchor = re.sub(r'[^a-z0-9 ]', '', anchor)  # Remove non-alphanumeric characters
    anchor = re.sub(r'\s+', '-', anchor)  # Replace spaces with dashes
    return anchor

def convert_and_adjust_links(html_content, domain):
    markdown_content = html_to_markdown(html_content)

    # Find headers in the Markdown content
    headers = re.findall(r'(?m)^(#{1,6})\s*(.*)', markdown_content)
    for level, header in headers:
        anchor = generate_anchor(header)
        header_with_anchor = f'{level} {header} {{#{anchor}}}'
        markdown_content = markdown_content.replace(f'{level} {header}', header_with_anchor)

    # Replace domain-specific links with anchor links
    # Assuming the links are of the form <a href="https://domain/path/to/page">
    markdown_content = re.sub(r'href="https?://' + re.escape(domain) + r'/([^"]+)"', r'href="#\1"', markdown_content)

    return markdown_content

def process_directory(start_file, directory, domain):
    if start_file not in os.listdir(directory):
        raise FileNotFoundError(f"Start file {start_file} not found in directory.")

    markdown_contents = []
    
    # Process the start file first
    with open(os.path.join(directory, start_file), 'r') as file:
        html_content = file.read()
        markdown_contents.append(convert_and_adjust_links(html_content, domain))

    # Process the rest of the files
    for filename in os.listdir(directory):
        if filename.endswith(".html") and filename != start_file:
            with open(os.path.join(directory, filename), 'r') as file:
                html_content = file.read()
                markdown_contents.append(convert_and_adjust_links(html_content, domain))

    return markdown_contents

if __name__ == "__main__":
    start_file = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
    directory = sys.argv[2] if len(sys.argv) > 2 else '.'
    domain = sys.argv[3] if len(sys.argv) > 3 else 'example.com'
    markdown_contents = process_directory(start_file, directory, domain)
    with open("combined_markdown.md", "w") as combined_file:
        combined_file.write("\n\n".join(markdown_contents))
