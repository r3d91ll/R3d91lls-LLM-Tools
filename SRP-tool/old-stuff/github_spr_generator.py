import os
import subprocess
import json
import logging
from pathlib import Path
import shutil
import html2text
import nbformat
import openai

# Initialization
def read_config(config_path='config.json'):
    """Reads configuration settings from a JSON file."""
    with open(config_path, 'r') as file:
        return json.load(file)

config = read_config()  # Load configuration settings

logging.basicConfig(filename=config['logging']['log_file'], 
                    level=config['logging']['log_level'])

class GitRepoManager:
    def __init__(self, config):
        self.repo_url = config['git']['repo_url']
        self.clone_directory = Path(config['git']['clone_directory'])

    def clone_or_update_repo(self):
        if self.clone_directory.exists():
            self._update_repo()
        else:
            self._clone_repo()

    def _clone_repo(self):
        try:
            subprocess.run(["git", "clone", self.repo_url, self.clone_directory], check=True)
            logging.info(f"Successfully cloned {self.repo_url} into {self.clone_directory}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to clone repository: {e}")
            raise

    def _update_repo(self):
        try:
            subprocess.run(["git", "-C", self.clone_directory, "pull", "origin", "main"], check=True)
            logging.info(f"Updated repository in {self.clone_directory}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to update repository: {e}")
            raise

class DirectoryManager:
    """
    Manages directories for storing cloned repositories and processed content.
    """

    def __init__(self, clone_directory, base_directory):
        """
        Initializes the DirectoryManager with the directory paths.
        :param clone_directory: The directory where the repository is cloned.
        :param base_directory: The base directory for creating SPR and working directories.
        """
        self.clone_directory = Path(clone_directory)
        self.spr_directory = Path(base_directory) / f"SPREnabled-{self.clone_directory.name}"
        self.working_directory = Path(base_directory) / f"working-{self.clone_directory.name}"

    def create_directories(self):
        """
        Creates the directory structure for the SPREnabled and working directories.
        """
        for directory in [self.spr_directory, self.working_directory]:
            if not directory.exists():
                directory.mkdir(parents=True)
                logging.info(f"Created directory: {directory}")

            self._mirror_directory_structure(self.clone_directory, directory)

    def _mirror_directory_structure(self, source, destination):
        for item in source.iterdir():
            if item.is_dir():
                dest_dir = destination / item.name
                dest_dir.mkdir(exist_ok=True)
                self._mirror_directory_structure(item, dest_dir)  # Recurse into subdirectories

    def remove_working_directory(self):
        """
        Removes the working-{reponame} directory.
        """
        if self.working_directory.exists():
            shutil.rmtree(self.working_directory)
            logging.info(f"Removed working directory: {self.working_directory}")

    # Additional methods for managing the directory contents can be added here

class ContentSorter:
    def __init__(self, clone_directory, spr_directory):
        """
        Initializes the ContentSorter with directory paths.
        :param clone_directory: The directory where the repository is cloned.
        :param spr_directory: The directory for storing SPR-enabled content (including code files).
        """
        self.clone_directory = Path(clone_directory)
        self.spr_directory = Path(spr_directory)
        self.markdown_processor = MarkdownProcessor(clone_directory, spr_directory)
        self.jupyter_processor = JupyterProcessor(clone_directory, spr_directory)

    def sort_content(self):
        """
        Processes all content in the cloned directory.
        """
        for item in self.clone_directory.rglob('*'):
            if item.is_file():
                if item.suffix == '.md':
                    self.markdown_processor.process_markdown_files()  # Corrected call
                elif item.suffix == '.ipynb':
                    self.jupyter_processor.process_jupyter_notebooks()  # Assuming similar structure
                else:
                    # Handle code and other file types by copying them to the SPR directory
                    self._copy_file_to_spr_directory(item)

    def _copy_file_to_spr_directory(self, file_path):
        """
        Copies a file to the SPR-enabled directory.
        :param file_path: Path to the file to be copied.
        """
        output_path = self.spr_directory / file_path.relative_to(self.clone_directory)
        output_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
        shutil.copy2(file_path, output_path)

class MarkdownProcessor:
    def __init__(self, clone_directory, working_directory):
        self.clone_directory = Path(clone_directory)
        self.working_directory = Path(working_directory)

    def process_markdown_files(self):
        for markdown_file in self.clone_directory.rglob('*.md'):
            self._process_single_file(markdown_file)

    def _process_single_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        processed_content = self._clean_up_markdown(content)
        output_path = self.working_directory / file_path.relative_to(self.clone_directory)
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(processed_content)

    def _clean_up_markdown(self, content):
        # Implement advanced de-linting and cleanup logic here
        return processed_content

class JupyterProcessor:
    def __init__(self, clone_directory, working_directory):
        self.clone_directory = Path(clone_directory)
        self.working_directory = Path(working_directory)

    def process_jupyter_notebooks(self):
        for notebook_file in self.clone_directory.rglob('*.ipynb'):
            self._process_single_notebook(notebook_file)

    def _process_single_notebook(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)

        html_content = self._convert_notebook_to_html(nb)
        cleaned_html = self._clean_html(html_content)
        markdown_content = html2text.html2text(cleaned_html)

        # Save the processed content
        output_path = self.working_directory / file_path.with_suffix('.md').name
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

    def _convert_notebook_to_html(self, notebook):
        html_exporter = HTMLExporter()
        html_exporter.template_name = 'basic'  # or other templates
        (body, _) = html_exporter.from_notebook_node(notebook)
        return body

    def _clean_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        # Perform necessary cleaning using BeautifulSoup
        return str(soup)

    def _convert_notebook_to_markdown(self, notebook):
        """
        Converts a Jupyter Notebook object to Markdown format.
        :param notebook: The Jupyter Notebook object.
        :return: Converted Markdown content.
        """
        markdown_content = ""
        for cell in notebook.cells:
            if cell.cell_type == 'markdown':
                markdown_content += cell.source + "\n\n"
            elif cell.cell_type == 'code':
                # Here, you can format code cells in a Markdown-friendly way
                markdown_content += "```python\n" + cell.source + "\n```\n\n"
                # Optionally handle the outputs of code cells here
        return markdown_content

    def _process_converted_markdown(self, markdown_content):
        """
        Processes the converted Markdown content (e.g., de-linting, formatting).
        :param markdown_content: Markdown content from a Jupyter Notebook.
        :return: Processed Markdown content.
        """
        # Implement any necessary processing of the Markdown content here
        # For example, you can call a MarkdownProcessor here for further processing
        return markdown_content

class SPRGenerator:
    """
    Converts content to SPR format using the SPR-Generator OpenAI assistant.
    """

    def __init__(self, openai_api_key, assistant_id):
        """
        Initializes the SPRGenerator with OpenAI API key and assistant ID.
        :param openai_api_key: OpenAI API key for authentication.
        :param assistant_id: ID of the SPR-Generator assistant.
        """
        self.openai_api_key = openai_api_key
        self.assistant_id = assistant_id
        openai.api_key = self.openai_api_key

    def generate_spr(self, content):
        """
        Converts the given content to SPR format using the OpenAI assistant.
        :param content: The content to be converted.
        :return: SPR formatted content.
        """
        try:
            response = openai.Completion.create(
                model="text-davinci-003",  # or other appropriate models
                prompt=content,
                temperature=0.7,
                max_tokens=2048,
                n=1,
                stop=None,
                engine=assistant_id
            )
            return response.choices[0].text.strip()
        except Exception as e:
            logging.error(f"Error in generating SPR: {e}")
            return None

    # Additional methods for handling specific SPR generation requirements can be added here

def main():
    """
    Main function to orchestrate the script execution.
    """
    # Load configuration
    config = read_config()

    # Initialize the GitRepoManager
    git_manager = GitRepoManager(config['git'])
    git_manager.clone_repo()

    # Initialize the DirectoryManager
    directory_manager = DirectoryManager(git_manager.clone_directory, Path(config['base_directory']))
    directory_manager.create_directories()

    # Initialize the ContentSorter
    content_processor = ContentSorter(git_manager.clone_directory, directory_manager.working_directory)
    content_processor.sort_content()

    # Initialize the SPRGenerator
    openai_api_key = os.getenv('OPENAI_API_KEY')
    assistant_id = config['spr_settings']['assistant_id']
    spr_generator = SPRGenerator(openai_api_key, assistant_id)

    # Process each file in the working directory and generate SPR content
    for content_file in directory_manager.working_directory.rglob('*'):
        if content_file.is_file() and content_file.suffix in ['.md', '.ipynb']:
            with open(content_file, 'r') as file:
                content = file.read()
                if spr_content := spr_generator.generate_spr(content):
                    # Save the SPR content in the appropriate SPR directory
                    spr_file_path = directory_manager.spr_directory / content_file.relative_to(directory_manager.working_directory)
                    with open(spr_file_path, 'w') as spr_file:
                        spr_file.write(spr_content)
                    logging.info(f"Saved SPR content to {spr_file_path}")

if __name__ == "__main__":
    main()

