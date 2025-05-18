import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import patch

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Function to simulate the validation logic in config.py
def validate_drives(drives):
    """
    Validate that drives is not empty and all paths exist.
    Returns a tuple (is_valid, error_message)
    """
    if not drives:
        return (
            False,
            "ERROR: DRIVES environment variable is empty or not set. Application startup failed.",
        )

    invalid_drives = []
    for drive in drives:
        if drive and not os.path.exists(drive):
            invalid_drives.append(drive)

    if invalid_drives:
        return (
            False,
            f"ERROR: The following drives do not exist or are not accessible: {', '.join(invalid_drives)}",
        )

    return True, None


def test_validate_drives_empty():
    """Test that validation fails when drives is empty."""
    is_valid, error_message = validate_drives([])
    assert not is_valid
    assert (
        error_message
        == "ERROR: DRIVES environment variable is empty or not set. Application startup failed."
    )


def test_validate_drives_invalid_paths():
    """Test that validation fails when drives contains invalid paths."""
    is_valid, error_message = validate_drives(
        ["/nonexistent/path1", "/nonexistent/path2"]
    )
    assert not is_valid
    assert (
        error_message
        == "ERROR: The following drives do not exist or are not accessible: /nonexistent/path1, /nonexistent/path2"
    )


def test_validate_drives_valid_paths():
    """Test that validation passes when drives contains valid paths."""
    # Create temporary directories for testing
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()

    try:
        is_valid, error_message = validate_drives([temp_dir1, temp_dir2])
        assert is_valid
        assert error_message is None
    finally:
        # Clean up the temporary directories
        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)


def test_config_validation_empty():
    """Test that main.py validation fails when DRIVES is empty."""
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    # Mock sys.exit to prevent the test from actually exiting
    with patch("sys.exit") as mock_exit, patch("builtins.print") as mock_print:
        try:
            # Unset the DRIVES environment variable
            if "DRIVES" in os.environ:
                del os.environ["DRIVES"]

            # Import the config module first to set up config.DRIVES
            import src.config
            import importlib

            importlib.reload(src.config)

            # Now import main and call validate_drives() explicitly
            import main

            importlib.reload(main)

            # Call validate_drives() which should exit with code 1
            main.validate_drives()

            # Check that sys.exit was called with exit code 1
            mock_exit.assert_called_once_with(1)
            # Check that the error message was printed (there might be other print calls)
            mock_print.assert_any_call(
                "ERROR: DRIVES environment variable is empty or not set. Application startup failed."
            )
        finally:
            # Restore the original DRIVES value
            if original_drives is not None:
                os.environ["DRIVES"] = original_drives
            else:
                if "DRIVES" in os.environ:
                    del os.environ["DRIVES"]


def test_config_validation_invalid_paths():
    """Test that main.py validation fails when DRIVES contains invalid paths."""
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    # Mock sys.exit to prevent the test from actually exiting
    with patch("sys.exit") as mock_exit, patch("builtins.print") as mock_print:
        try:
            # Set the DRIVES environment variable with non-existent paths
            os.environ["DRIVES"] = "/nonexistent/path1,/nonexistent/path2"

            # Import the config module first to set up config.DRIVES
            import src.config
            import importlib

            importlib.reload(src.config)

            # Now import main and call validate_drives() explicitly
            import main

            importlib.reload(main)

            # Call validate_drives() which should exit with code 1
            main.validate_drives()

            # Check that sys.exit was called with exit code 1
            mock_exit.assert_called_once_with(1)
            # Check that the error message was printed (there might be other print calls)
            mock_print.assert_any_call(
                "ERROR: The following drives do not exist or are not accessible: /nonexistent/path1, /nonexistent/path2"
            )
        finally:
            # Restore the original DRIVES value
            if original_drives is not None:
                os.environ["DRIVES"] = original_drives
            else:
                if "DRIVES" in os.environ:
                    del os.environ["DRIVES"]


def test_config_validation_valid_paths():
    """Test that main.py validation passes when DRIVES contains valid paths."""
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    # Create temporary directories for testing
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()

    try:
        # Set the DRIVES environment variable with the temporary directories
        os.environ["DRIVES"] = f"{temp_dir1},{temp_dir2}"

        # Import the config module first to set up config.DRIVES
        import src.config
        import importlib

        importlib.reload(src.config)
        from src.config import config

        # Now import main which will validate config.DRIVES
        import main

        importlib.reload(main)

        # Check that DRIVES is correctly loaded
        assert config.DRIVES == [temp_dir1, temp_dir2]
    finally:
        # Restore the original DRIVES value
        if original_drives is not None:
            os.environ["DRIVES"] = original_drives
        else:
            if "DRIVES" in os.environ:
                del os.environ["DRIVES"]

        # Clean up the temporary directories
        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)
