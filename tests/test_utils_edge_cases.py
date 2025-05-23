import sys
import os
import tempfile
import pytest
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modern.utils import (
    find_latest_modification_time,
    extract_serial_number,
    parse_sample_name,
)


def test_find_latest_modification_time_nonexistent_directory():
    """Test that find_latest_modification_time raises an appropriate exception when the directory doesn't exist."""
    with pytest.raises(FileNotFoundError):
        find_latest_modification_time(Path("/nonexistent/directory"))


def test_extract_serial_number_none():
    """Test that extract_serial_number handles None input appropriately."""
    with pytest.raises(AttributeError):
        extract_serial_number(None)


def test_extract_serial_number_non_string():
    """Test that extract_serial_number handles non-string input appropriately."""
    with pytest.raises(AttributeError):
        extract_serial_number(123)


def test_parse_sample_name_none():
    """Test that parse_sample_name handles None input appropriately."""
    with pytest.raises(AttributeError):
        parse_sample_name(None)


def test_parse_sample_name_non_string():
    """Test that parse_sample_name handles non-string input appropriately."""
    with pytest.raises(AttributeError):
        parse_sample_name(123)
