import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from legacy.drives import get_drive_path


def test_get_drive_path_found():
    """Test that get_drive_path returns the correct path when the drive name is found."""
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    # Create temporary directories for testing
    temp_dir1 = tempfile.mkdtemp(prefix="drive1_")
    temp_dir2 = tempfile.mkdtemp(prefix="drive2_")

    try:
        # Set the DRIVES environment variable with the temporary directories
        os.environ["DRIVES"] = f"{temp_dir1},{temp_dir2}"

        # Import the config module to set up config.DRIVES
        import config_rdr
        import importlib

        importlib.reload(config_rdr)

        # Get the drive name (last component of the path)
        drive1_name = Path(temp_dir1).name
        drive2_name = Path(temp_dir2).name

        # Test that get_drive_path returns the correct path for each drive
        assert get_drive_path(drive1_name) == Path(temp_dir1)
        assert get_drive_path(drive2_name) == Path(temp_dir2)
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


def test_get_drive_path_not_found():
    """Test that get_drive_path returns None when the drive name is not found."""
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()

    try:
        # Set the DRIVES environment variable with the temporary directory
        os.environ["DRIVES"] = temp_dir

        # Import the config module to set up config.DRIVES
        import config_rdr
        from config_rdr import config
        import importlib

        importlib.reload(config_rdr)

        # Test that get_drive_path returns None for a non-existent drive name
        assert get_drive_path("nonexistent_drive") is None
    finally:
        # Restore the original DRIVES value
        if original_drives is not None:
            os.environ["DRIVES"] = original_drives
        else:
            if "DRIVES" in os.environ:
                del os.environ["DRIVES"]

        # Clean up the temporary directory
        shutil.rmtree(temp_dir)


def test_get_drive_path_empty_drives():
    """Test that get_drive_path returns None when DRIVES is empty."""
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    try:
        # Unset the DRIVES environment variable
        if "DRIVES" in os.environ:
            del os.environ["DRIVES"]

        # Import the config module to set up config.DRIVES
        import config_rdr
        import importlib

        importlib.reload(config_rdr)

        # Test that get_drive_path returns None when DRIVES is empty
        assert get_drive_path("any_drive") is None
    finally:
        # Restore the original DRIVES value
        if original_drives is not None:
            os.environ["DRIVES"] = original_drives
        else:
            if "DRIVES" in os.environ:
                del os.environ["DRIVES"]
