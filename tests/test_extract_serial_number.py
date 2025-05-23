import sys
import os
import pytest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.modern.from_legacy import extract_serial_number


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
