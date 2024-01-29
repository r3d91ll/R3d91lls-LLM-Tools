import html2text
import os
import sys

def html_to_markdown(html_content):
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    return converter.handle(html_content)

def convert_directory_to_markdown(directory):
    markdown_files_content = []
    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            with open(os.path.join(directory, filename), 'r') as file:
                html_content = file.read()
                markdown_content = html_to_markdown(html_content)
                markdown_files_content.append(markdown_content)
    return markdown_files_content

if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    markdown_contents = convert_directory_to_markdown(directory)
    with open("combined_markdown.md", "w") as combined_file:
        combined_file.write("\n\n".join(markdown_contents))


""" Execution Steps

    Place the Script in the Desired Directory: Save the above script in a file, say html_to_md_converter.py, and place it in the same directory as your HTML files.

    Run the Script: Open a terminal in this directory and run the script with the following command:
    # python html_to_md_converter.py
    
    Optionally, you can specify a different directory containing HTML files:
    # python html_to_md_converter.py /path/to/html/files
    
    Check the Output: After execution, you'll find a file named combined_markdown.md in the same directory, containing the concatenated Markdown content of all HTML files. 
"""