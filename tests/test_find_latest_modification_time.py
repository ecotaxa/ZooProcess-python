import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modern.utils import find_latest_modification_time


def test_find_latest_modification_time():
    """Test that find_latest_modification_time returns the latest modification time of any file in a directory tree."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a subdirectory
        subdir = temp_path / "subdir"
        subdir.mkdir()

        # Create some files with different modification times
        file1 = temp_path / "file1.txt"
        file2 = subdir / "file2.txt"
        file3 = subdir / "file3.txt"

        # Write to the files
        file1.write_text("File 1")
        file2.write_text("File 2")
        file3.write_text("File 3")

        # Set modification times with delays to ensure they're different
        # First file: current time
        current_time = time.time()
        os.utime(file1, (current_time, current_time))

        # Second file: 1 second later
        time.sleep(1)
        file2_time = time.time()
        os.utime(file2, (file2_time, file2_time))

        # Third file: 1 second later
        time.sleep(1)
        file3_time = time.time()
        os.utime(file3, (file3_time, file3_time))

        # Get the latest modification time
        latest_time = find_latest_modification_time(temp_path)

        # Check that it's the time of the third file (the latest)
        expected_time = datetime.fromtimestamp(file3_time)
        assert (
            latest_time == expected_time
        ), f"Expected {expected_time}, got {latest_time}"


def test_find_latest_modification_time_empty_directory():
    """Test that find_latest_modification_time returns the directory's modification time if no files are found."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Get the directory's modification time
        dir_time = os.path.getmtime(temp_dir)

        # Get the latest modification time
        latest_time = find_latest_modification_time(temp_path)

        # Check that it's the directory's modification time
        expected_time = datetime.fromtimestamp(dir_time)
        assert (
            latest_time == expected_time
        ), f"Expected {expected_time}, got {latest_time}"


def test_find_latest_modification_time_with_inaccessible_files(monkeypatch):
    """Test that find_latest_modification_time handles inaccessible files gracefully."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a file
        file1 = temp_path / "file1.txt"
        file1.write_text("File 1")

        # Set its modification time
        file1_time = time.time()
        os.utime(file1, (file1_time, file1_time))

        # Mock os.path.getmtime to raise an exception for a specific file
        original_getmtime = os.path.getmtime

        def mock_getmtime(path):
            if "file1.txt" in path:
                raise PermissionError("Permission denied")
            return original_getmtime(path)

        monkeypatch.setattr(os.path, "getmtime", mock_getmtime)

        # Get the latest modification time
        latest_time = find_latest_modification_time(temp_path)

        # Check that it's the directory's modification time (since the file is inaccessible)
        dir_time = original_getmtime(temp_dir)
        expected_time = datetime.fromtimestamp(dir_time)
        assert (
            latest_time == expected_time
        ), f"Expected {expected_time}, got {latest_time}"
