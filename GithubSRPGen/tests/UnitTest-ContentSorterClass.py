import unittest
from pathlib import Path
from shutil import rmtree
from unittest.mock import MagicMock
from github_spr_generator import ContentSorter

class TestContentSorter(unittest.TestCase):

    def setUp(self):
        self.base_path = Path.cwd()
        self.clone_directory = self.base_path / "test/autogen"
        self.spr_directory = self.base_path / "SPREnabled-autogen"
        self.working_directory = self.base_path / "working-autogen"
        self.content_sorter = ContentSorter(self.clone_directory, self.spr_directory)

        # Mock the MarkdownProcessor and JupyterProcessor
        self.content_sorter.markdown_processor = MagicMock()
        self.content_sorter.jupyter_processor = MagicMock()

        # Prepare the directories
        self.spr_directory.mkdir(parents=True, exist_ok=True)
        self.working_directory.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        # Clean up created files in working directory
        if self.working_directory.exists():
            rmtree(self.working_directory)

    def test_sort_content(self):
        self.content_sorter.sort_content()

        if markdown_files := list(self.clone_directory.rglob('*.md')):
            self.content_sorter.markdown_processor.process_markdown_files.assert_called_once()
        else:
            self.content_sorter.markdown_processor.process_markdown_files.assert_not_called()

        if notebook_files := list(self.clone_directory.rglob('*.ipynb')):
            self.content_sorter.jupyter_processor.process_jupyter_notebooks.assert_called_once()
        else:
            self.content_sorter.jupyter_processor.process_jupyter_notebooks.assert_not_called()

        # Check if non-Markdown and non-Jupyter files are copied to SPREnabled directory
        for file in self.clone_directory.rglob('*'):
            if file.is_file() and file.suffix not in ['.md', '.ipynb']:
                expected_path = self.spr_directory / file.relative_to(self.clone_directory)
                self.assertTrue(expected_path.exists(), f"File {file} was not copied correctly")

if __name__ == '__main__':
    unittest.main()
