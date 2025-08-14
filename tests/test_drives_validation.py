import os
import shutil
import tempfile
from pathlib import Path

from pytest_mock import MockFixture

import legacy.drives

from contextlib import contextmanager


@contextmanager
def drives_env(value: str | None):
    original_drives = os.environ.get("DRIVES")
    try:
        if value is None:
            # Set to empty string so python-dotenv does not override with .env values
            os.environ["DRIVES"] = ""
        else:
            os.environ["DRIVES"] = value
        yield
    finally:
        if original_drives is not None:
            os.environ["DRIVES"] = original_drives
        else:
            os.environ.pop("DRIVES", None)


def reload_config_module():
    import importlib
    import config_rdr
    import legacy.drives as legacy_drives_mod

    importlib.reload(config_rdr)
    # Also reload legacy.drives to ensure it uses the refreshed config object
    importlib.reload(legacy_drives_mod)


def expect_validate_exits(mocker: MockFixture):
    mock_exit = mocker.patch("legacy.drives.sys.exit")

    legacy.drives.validate_drives()

    mock_exit.assert_called_once_with(1)


def test_config_validation_empty(mocker: MockFixture):
    """Test that validation fails when DRIVES is empty."""
    with drives_env(None):
        reload_config_module()
        expect_validate_exits(mocker)


def test_config_validation_invalid_paths(mocker: MockFixture):
    """Test that validation fails when DRIVES contains invalid paths."""
    with drives_env("/nonexistent/path1,/nonexistent/path2"):
        reload_config_module()
        expect_validate_exits(mocker)


def test_config_validation_valid_paths():
    """Test that validation passes when DRIVES contains valid paths."""
    # Create temporary directories for testing
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()

    try:
        with drives_env(f"{temp_dir1},{temp_dir2}"):
            reload_config_module()
            from config_rdr import config

            # Check that DRIVES is correctly loaded
            assert config.get_drives() == [Path(temp_dir1), Path(temp_dir2)]
    finally:
        # Clean up the temporary directories
        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)


def test_config_validation_not_directories(mocker: MockFixture):
    """Test that validation fails when DRIVES contains paths that are not directories."""
    # Create a temporary directory and a temporary file
    temp_dir = tempfile.mkdtemp()
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()

    try:
        with drives_env(f"{temp_dir},{temp_file.name}"):
            reload_config_module()
            expect_validate_exits(mocker)
    finally:
        # Clean up the temporary directory and file
        shutil.rmtree(temp_dir)
        os.unlink(temp_file.name)


def test_config_validation_duplicates(mocker: MockFixture):
    """Test that validation fails when DRIVES contains duplicate paths."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        with drives_env(f"{temp_dir},{temp_dir}"):
            reload_config_module()
            expect_validate_exits(mocker)
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)
