import os
import re

def clean_file(original_file_path, new_directory):
    with open(original_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Remove specific patterns
    content = re.sub(r'[🌜🌞]', '', content)  # Remove emoji characters

    # Remove markdown links for edit, previous, next, community, etc.
    patterns_to_remove = [
        r'\[ Edit this page.*?\]\(.*?\)',
        r'\[ Previous .*?\]\(.*?\)',
        r'\[ Next .*?\]\(.*?\)',
        r'\[.*?\]\(https://discord.gg/.*?\)',
        r'\[.*?\]\(https://twitter.com/.*?\)',
        r'\[ Privacy and Cookies.*?\]\(.*?\)'
    ]
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content)

    # Creating the new filename in the 'clean_docs' directory
    new_file_path = os.path.join(new_directory, os.path.basename(original_file_path))

    # Write the cleaned content to the new file
    with open(new_file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def clean_directory(directory):
    clean_directory = os.path.join(directory, 'clean_docs')
    if not os.path.exists(clean_directory):
        os.makedirs(clean_directory)

    for filename in os.listdir(directory):
        if filename.endswith('.md'):
            file_path = os.path.join(directory, filename)
            clean_file(file_path, clean_directory)
            print(f"Cleaned {filename}")

if __name__ == "__main__":
    directory = input("Enter the directory path containing the markdown files: ")
    clean_directory(directory)
