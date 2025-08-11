import sys
import os
import pytest

from modern.utils import extract_serial_number


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
