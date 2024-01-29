import unittest
import os
from shutil import rmtree
from github_spr_generator import DirectoryManager

class TestDirectoryManager(unittest.TestCase):
    
    def setUp(self):
        # Set up the base directory for the test (current working directory)
        self.base_path = os.getcwd()
        # Set up the clone directory as a subdirectory within the current working directory
        self.test_clone_dir = os.path.join(self.base_path, "autogen")
        self.repo_name = "autogen"
        # Initialize the DirectoryManager with the base directory as the current working directory
        self.directory_manager = DirectoryManager(self.test_clone_dir, self.base_path)

    # def tearDown(self):
    #     # Clean up created directories after tests
    #     SPREnabled_dir = os.path.join(self.base_path, f"SPREnabled-{self.repo_name}")
    #     working_dir = os.path.join(self.base_path, f"working-{self.repo_name}")
    #     if os.path.exists(SPREnabled_dir):
    #         rmtree(SPREnabled_dir)
    #     if os.path.exists(working_dir):
    #         rmtree(working_dir)

    def test_directory_creation(self):
        # Test whether the directories are created correctly
        self.directory_manager.create_directories()
        SPREnabled_dir = os.path.join(self.base_path, f"SPREnabled-{self.repo_name}")
        working_dir = os.path.join(self.base_path, f"working-{self.repo_name}")
        self.assertTrue(os.path.exists(SPREnabled_dir))
        self.assertTrue(os.path.exists(working_dir))

    # Additional tests...

if __name__ == '__main__':
    unittest.main()
