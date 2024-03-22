import unittest
from pathlib import Path
import shutil
import logging
from github_spr_generator import DirectoryManager

class TestDirectoryManager(unittest.TestCase):

    def setUp(self):
        # Setup paths for the test
        self.clone_directory = Path("autogen")
        self.base_directory = Path(".")

        # Initialize DirectoryManager
        self.manager = DirectoryManager(clone_directory=self.clone_directory, base_directory=self.base_directory)

        # Ensure base directories exist
        self.base_directory.mkdir(parents=True, exist_ok=True)

        # Add mock content to clone_directory for testing
        (self.clone_directory / "test_dir").mkdir(exist_ok=True)
        (self.clone_directory / "test_dir/test_file.txt").touch()

    def test_create_directories(self):
        # Test creation of directories and mirroring structure
        self.manager.create_directories()
        self.assertTrue((self.manager.spr_directory / "test_dir").exists())
        self.assertTrue((self.manager.spr_directory / "test_dir/test_file.txt").exists())
        self.assertTrue((self.manager.working_directory / "test_dir").exists())

    def test_remove_working_directory(self):
        # Test removal of working directory
        self.manager.create_directories()
        self.manager.remove_working_directory()
        self.assertFalse(self.manager.working_directory.exists())

    def tearDown(self):
        # Cleanup after tests but keep the autogen directory intact
        if self.base_directory.exists() and self.base_directory.is_dir():
            try:
                shutil.rmtree(self.base_directory)
            except Exception as e:
                logging.error(f"Error occurred during tearDown: {e}")

if __name__ == '__main__':
    unittest.main()
