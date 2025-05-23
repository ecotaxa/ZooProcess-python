import re
import pytest


def extract_serial_number(project_name: str) -> str:
    """
    Extract the serial number (sn) from the project name.
    It can be in the end of the name or in the middle.
    Default to 'sn???' if not found.

    Args:
        project_name: The name of the project

    Returns:
        The extracted serial number or 'sn???' if not found
    """
    # Look for 'sn' followed by digits in the project name
    match = re.search(r"sn\d+", project_name.lower())
    if match:
        return match.group(0)
    return "sn???"


def test_extract_serial_number_end():
    # Test with serial number at the end
    project_name = "Zooscan_apero_pp_2023_wp2_sn002"
    assert extract_serial_number(project_name) == "sn002"


def test_extract_serial_number_middle():
    # Test with serial number in the middle
    project_name = "Zooscan_sn123_apero_pp_2023_wp2"
    assert extract_serial_number(project_name) == "sn123"


def test_extract_serial_number_not_found():
    # Test with no serial number
    project_name = "Zooscan_apero_pp_2023_wp2"
    assert extract_serial_number(project_name) == "sn???"


def test_extract_serial_number_case_insensitive():
    # Test with different case
    project_name = "Zooscan_apero_pp_2023_wp2_SN002"
    assert extract_serial_number(project_name) == "sn002"
