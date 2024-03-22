import pytest
from pytest_mock import mocker
import os
from pathlib import Path
from github_spr_generator import ContentProcessor, MarkdownProcessor, JupyterProcessor

# Constants for test directories
CLONE_DIR = '/tmp/clone_dir'
SPR_DIR = '/tmp/spr_dir'

# Test IDs for parametrization
HAPPY_PATH_ID = 'happy_path'
EDGE_CASE_EMPTY_DIR_ID = 'edge_case_empty_dir'
ERROR_CASE_INVALID_DIR_ID = 'error_case_invalid_dir'

@pytest.fixture
def setup_directories(tmp_path):
    """
    Fixture to set up and tear down temporary directories for testing.
    """
    clone_dir = tmp_path / 'clone_dir'
    spr_dir = tmp_path / 'spr_dir'
    clone_dir.mkdir()
    spr_dir.mkdir()
    return clone_dir, spr_dir

@pytest.mark.parametrize("test_id, clone_dir_content, expected_spr_dir_content", [
    (HAPPY_PATH_ID, {'test.md': 'Markdown content', 'test.ipynb': '{"key": "value"}', 'code.py': 'print("Hello, World!")'}, {'test.md', 'test.ipynb', 'code.py'}),
    (EDGE_CASE_EMPTY_DIR_ID, {}, set()),
    # Assuming that the error case is when the directories do not exist or are not accessible
    (ERROR_CASE_INVALID_DIR_ID, None, None),
])
def test_process_content(test_id, clone_dir_content, expected_spr_dir_content, setup_directories, mocker):
    clone_dir, spr_dir = setup_directories

    # Arrange
    if clone_dir_content is not None:
# sourcery skip: no-loop-in-tests
        for file_name, content in clone_dir_content.items():
            (clone_dir / file_name).write_text(content)

    # Mocking the processors to avoid testing their internal behavior here
    mocked_markdown_processor = mocker.patch.object(MarkdownProcessor, 'process_markdown_files')
    mocked_jupyter_processor = mocker.patch.object(JupyterProcessor, 'process_jupyter_notebooks')

    processor = ContentProcessor(clone_dir, spr_dir)

    # Act
# sourcery skip: no-conditionals-in-tests
    if test_id == ERROR_CASE_INVALID_DIR_ID:
        with pytest.raises(Exception):
            processor.process_content()
    else:
        processor.process_content()

    # Assert
# sourcery skip: no-conditionals-in-tests
    if test_id != ERROR_CASE_INVALID_DIR_ID:
        spr_dir_files = {p.name for p in spr_dir.rglob('*') if p.is_file()}
        expected_spr_dir_content = {'code.py', 'test.ipynb', 'test.md'}

        assert spr_dir_files == expected_spr_dir_content
        if 'test.md' in clone_dir_content:
            mocked_markdown_processor.assert_called_once()
        if 'test.ipynb' in clone_dir_content:
            mocked_jupyter_processor.assert_called_once()
