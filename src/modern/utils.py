import os
import re
from datetime import datetime
from pathlib import Path


def find_latest_modification_time(directory_path: Path) -> datetime:
    """
    Find the most recent modification time of any file in the directory tree.

    Args:
        directory_path: The path to the directory to search

    Returns:
        The most recent modification time as a datetime object
    """
    latest_time = 0.0

    # Walk through all directories and files
    join, getmtime = os.path.join, os.path.getmtime
    for root, _, files in os.walk(str(directory_path)):
        for file in files:
            file_path = join(root, file)
            try:
                # Get the modification time of the file
                mtime = getmtime(file_path)
                if mtime > latest_time:
                    latest_time = mtime
            except (OSError, PermissionError):
                # Skip files that can't be accessed
                continue

    # If no files were found, return the directory's modification time
    if latest_time == 0:
        latest_time = os.path.getmtime(str(directory_path))

    return datetime.fromtimestamp(latest_time)


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


def parse_sample_name(sample_name: str) -> dict:
    """
    Parse a sample name into its components.
    Sample names follow the structure: [program]_[ship]_[net_type]_[optional_mesh_size]_[cruise_number]_st[station_id]_[day_night]_n[net_number]_d[fraction_type]_[fraction_number]_sur_[total_fractions]_[scan_number]
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
    parsed = {}

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
        parsed["net_type"] = components[idx]
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


def convert_ddm_to_decimal_degrees(a_value):
    """
    Convert a coordinate from Degrees Decimal Minutes (DDM) format to Decimal Degrees (DD) format.

    In DDM format, the decimal part represents minutes divided by 100 (e.g., 45.30 means 45 degrees and 30 minutes).
    This function converts it to decimal degrees where minutes are divided by 60 (e.g., 45.5 degrees).

    The conversion formula is: DD = degrees + (minutes/60)
    Which is implemented as: degrees + (decimal_part * 100/60)/100

    Args:
        a_value: A coordinate value in DDM format (e.g., 45.30 for 45°30')

    Returns:
        The coordinate converted to decimal degrees format (e.g., 45.50 for 45.5°)
        If the input cannot be converted to a float, returns the original value.

    Examples:
        >>> convert_ddm_to_decimal_degrees(45.30)
        45.5
        >>> convert_ddm_to_decimal_degrees(10.3030)
        10.505
    """
    val = float(a_value)
    degrees = int(val)
    decimal = (val - degrees) * 100
    decimal = round(decimal / 30 * 50, 4)
    return degrees + decimal / 100
