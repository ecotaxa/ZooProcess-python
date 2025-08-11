import pytest

from modern.utils import (
    extract_serial_number,
    parse_sample_name,
)


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
