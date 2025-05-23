import sys
import os
import pytest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modern.utils import parse_sample_name


def test_parse_sample_name_full():
    # Test with a full sample name including all components
    sample_name = "apero2023_tha_bioness_sup2000_017_st66_d_n1_d3_1_sur_4_1"
    parsed = parse_sample_name(sample_name)

    assert parsed["full_name"] == sample_name
    assert parsed["num_components"] == 13
    assert parsed["program"] == "apero2023"
    assert parsed["ship"] == "tha"
    assert parsed["nettype"] == "bioness"
    assert parsed["mesh_size"] == "sup2000"
    assert parsed["cruise_number"] == "017"
    assert parsed["station_id"] == "st66"
    assert parsed["day_night"] == "d"
    assert parsed["net_number"] == "n1"
    assert parsed["fraction_type"] == "d3"
    assert parsed["fraction_number"] == "1"
    assert parsed["total_fractions_prefix"] == "sur"
    assert parsed["total_fractions"] == "4"
    assert parsed["scan_number"] == "1"


def test_parse_sample_name_without_mesh_size():
    # Test with a sample name without the optional mesh size
    sample_name = "apero2023_tha_bioness_017_st66_d_n1_d3_1_sur_4_1"
    parsed = parse_sample_name(sample_name)

    assert parsed["full_name"] == sample_name
    assert parsed["num_components"] == 12
    assert parsed["program"] == "apero2023"
    assert parsed["ship"] == "tha"
    assert parsed["nettype"] == "bioness"
    assert "mesh_size" not in parsed
    assert parsed["cruise_number"] == "017"
    assert parsed["station_id"] == "st66"
    assert parsed["day_night"] == "d"
    assert parsed["net_number"] == "n1"
    assert parsed["fraction_type"] == "d3"
    assert parsed["fraction_number"] == "1"
    assert parsed["total_fractions_prefix"] == "sur"
    assert parsed["total_fractions"] == "4"
    assert parsed["scan_number"] == "1"


def test_parse_sample_name_partial():
    # Test with a partial sample name
    sample_name = "apero2023_tha_bioness"
    parsed = parse_sample_name(sample_name)

    assert parsed["full_name"] == sample_name
    assert parsed["num_components"] == 3
    assert parsed["program"] == "apero2023"
    assert parsed["ship"] == "tha"
    assert parsed["nettype"] == "bioness"
    assert "mesh_size" not in parsed
    assert "cruise_number" not in parsed
    assert "station_id" not in parsed
    assert "day_night" not in parsed
    assert "net_number" not in parsed
    assert "fraction_type" not in parsed
    assert "fraction_number" not in parsed
    assert "total_fractions_prefix" not in parsed
    assert "total_fractions" not in parsed
    assert "scan_number" not in parsed


def test_parse_sample_name_single():
    # Test with a single component
    sample_name = "apero2023"
    parsed = parse_sample_name(sample_name)

    assert parsed["full_name"] == sample_name
    assert parsed["num_components"] == 1
    assert parsed["program"] == "apero2023"
    assert "ship" not in parsed
    assert "nettype" not in parsed
    assert "mesh_size" not in parsed
    assert "cruise_number" not in parsed
    assert "station_id" not in parsed
    assert "day_night" not in parsed
    assert "net_number" not in parsed
    assert "fraction_type" not in parsed
    assert "fraction_number" not in parsed
    assert "total_fractions_prefix" not in parsed
    assert "total_fractions" not in parsed
    assert "scan_number" not in parsed


def test_parse_sample_name_empty():
    # Test with an empty string
    sample_name = ""
    parsed = parse_sample_name(sample_name)

    assert parsed["full_name"] == sample_name
    assert parsed["num_components"] == 1  # Split on empty string gives ['']
    assert parsed["components"] == [""]
