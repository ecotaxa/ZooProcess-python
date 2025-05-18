import os
import sys
import pytest
import importlib
from unittest.mock import patch

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_drives_empty_fails():
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

            # Reload the config module again to restore the original state
            importlib.reload(src.config)


def test_drives_with_invalid_paths_fails():
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    # Mock sys.exit to prevent the test from actually exiting
    with patch("sys.exit") as mock_exit, patch("builtins.print") as mock_print:
        try:
            # Set the DRIVES environment variable with non-existent paths
            os.environ["DRIVES"] = "/nonexistent/path1,/nonexistent/path2"

            # Import the config module first to set up config.DRIVES
            import src.config

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
                del os.environ["DRIVES"]

            # Reload the config module again to restore the original state
            importlib.reload(src.config)


def test_drives_with_valid_paths():
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    # Create temporary directories for testing
    import tempfile

    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()

    try:
        # Set the DRIVES environment variable with the temporary directories
        os.environ["DRIVES"] = f"{temp_dir1},{temp_dir2}"

        # Import the config module first to set up config.DRIVES
        import src.config

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
            del os.environ["DRIVES"]

        # Clean up the temporary directories
        import shutil

        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)

        # Reload the config module again to restore the original state
        importlib.reload(src.config)
