import pytest


def parse_sample_name(sample_name: str) -> dict:
    """
    Parse a sample name into its components.
    Sample names follow the structure: [program]_[ship]_[nettype]_[optional_mesh_size]_[cruise_number]_st[station_id]_[day_night]_n[net_number]_d[fraction_type]_[fraction_number]_sur_[total_fractions]_[scan_number]
    Example: apero2023_tha_bioness_sup2000_017_st66_d_n1_d3_1_sur_4_1

    Components Breakdown:
    1. Program: Scientific program name, often with year (e.g., `apero2023`)
    2. Ship: Abbreviated ship name (e.g., `tha` for thalassa)
    3. Net Type: Type of sampling net (e.g., `bioness`)
    4. Optional Mesh Size: Sometimes includes mesh size (e.g., `sup2000`)
    5. Cruise Number: Numbered cruise identifier (e.g., `013`, `014`, `017`)
    6. Station ID: Station identifier with prefix (e.g., `st46`, `st66`)
    7. Day/Night: Sampling time - `d` (day) or `n` (night)
    8. Net Number: Specific net used with prefix (e.g., `n1`, `n2`, `n9`)
    9. Fraction Type: Type of fraction with prefix (e.g., `d1`, `d2`, `d3`)
    10. Fraction Number: Sequential number of this fraction (e.g., `1`, `2`, `8`)
    11. Total Fractions: Total number of fractions with prefix (e.g., `sur_1`, `sur_4`, `sur_8`)
    12. Scan Number: Sequential scan number (typically `1`)

    Args:
        sample_name: The name of the sample

    Returns:
        A dictionary containing the parsed components of the sample name
    """
    components = sample_name.split("_")
    parsed = {
        "full_name": sample_name,
        "components": components,
        "num_components": len(components),
    }

    # Initialize component index
    idx = 0

    # Try to assign meaning to components based on position and patterns
    if idx < len(components):
        parsed["program"] = components[idx]
        idx += 1

    if idx < len(components):
        parsed["ship"] = components[idx]
        idx += 1

    if idx < len(components):
        parsed["nettype"] = components[idx]
        idx += 1

    # Check for optional mesh size (if present)
    if idx < len(components) and components[idx].startswith("sup"):
        parsed["mesh_size"] = components[idx]
        idx += 1

    if idx < len(components):
        parsed["cruise_number"] = components[idx]
        idx += 1

    if idx < len(components) and components[idx].startswith("st"):
        parsed["station_id"] = components[idx]
        idx += 1

    if idx < len(components) and (components[idx] == "d" or components[idx] == "n"):
        parsed["day_night"] = components[idx]
        idx += 1

    if idx < len(components) and components[idx].startswith("n"):
        parsed["net_number"] = components[idx]
        idx += 1

    if idx < len(components) and components[idx].startswith("d"):
        parsed["fraction_type"] = components[idx]
        idx += 1

    if idx < len(components):
        parsed["fraction_number"] = components[idx]
        idx += 1

    # Check for "sur_X" pattern for total fractions
    if idx + 1 < len(components) and components[idx] == "sur":
        parsed["total_fractions_prefix"] = components[idx]
        idx += 1
        parsed["total_fractions"] = components[idx]
        idx += 1

    if idx < len(components):
        parsed["scan_number"] = components[idx]

    return parsed


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
