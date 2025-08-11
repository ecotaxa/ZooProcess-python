import pytest
from datetime import datetime

from modern.from_legacy import parse_legacy_date


def test_parse_legacy_date_valid():
    """Test parse_legacy_date with valid date strings."""
    # Test with a valid date string
    date_str = "20230101_1200"
    result = parse_legacy_date(date_str)

    # Verify the result is a datetime object
    assert isinstance(result, datetime)

    # Verify the parsed date components
    assert result.year == 2023
    assert result.month == 1
    assert result.day == 1
    assert result.hour == 12
    assert result.minute == 0
    assert result.second == 0

    # Test with another valid date string
    date_str = "20221231_2359"
    result = parse_legacy_date(date_str)

    # Verify the result is a datetime object
    assert isinstance(result, datetime)

    # Verify the parsed date components
    assert result.year == 2022
    assert result.month == 12
    assert result.day == 31
    assert result.hour == 23
    assert result.minute == 59
    assert result.second == 0


def test_parse_legacy_date_invalid_format():
    """Test parse_legacy_date with invalid date formats."""
    # Define the epoch date for comparison
    epoch_date = datetime(1970, 1, 1)

    # Test with an invalid date format (wrong separator)
    result = parse_legacy_date("20230101-1200")
    assert result == epoch_date

    # Test with an invalid date format (missing time)
    result = parse_legacy_date("20230101")
    assert result == epoch_date

    # Test with an invalid date format (wrong order)
    result = parse_legacy_date("1200_20230101")
    assert result == epoch_date

    # Test with an invalid date format (extra characters)
    result = parse_legacy_date("20230101_1200_extra")
    assert result == epoch_date

    # Test with an invalid date format (letters instead of numbers)
    result = parse_legacy_date("abcdefgh_ijkl")
    assert result == epoch_date


def test_parse_legacy_date_edge_cases():
    """Test parse_legacy_date with edge cases."""
    # Define the epoch date for comparison
    epoch_date = datetime(1970, 1, 1)

    # Test with an empty string
    result = parse_legacy_date("")
    assert result == epoch_date

    # Test with None
    result = parse_legacy_date(None)
    assert result == epoch_date

    # Test with a non-string value
    result = parse_legacy_date(12345)
    assert result == epoch_date

    # Test with a date that doesn't exist (February 30)
    result = parse_legacy_date("20230230_1200")
    assert result == epoch_date

    # Test with an invalid hour (24)
    result = parse_legacy_date("20230101_2400")
    assert result == epoch_date

    # Test with an invalid minute (60)
    result = parse_legacy_date("20230101_1260")
    assert result == epoch_date
