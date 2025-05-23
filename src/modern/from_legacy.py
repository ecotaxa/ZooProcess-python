#
# Transformers from Legacy data to modern models
#
import re
from pathlib import Path

from Models import Project, Drive, Sample
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder, ZooscanDrive


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


def project_from_legacy(
    drive_model: Drive, a_prj_path: Path, serial_number: str = None
):
    unq_id = f"{drive_model.name}|{a_prj_path.name}"

    # Extract serial number from project name if not provided
    if serial_number is None:
        serial_number = extract_serial_number(a_prj_path.name)

    zoo_project = ZooscanDrive(Path(drive_model.url)).get_project_folder(
        a_prj_path.name
    )
    sample_models = samples_from_legacy_project(zoo_project)
    project = Project(
        path=str(a_prj_path),
        id=unq_id,
        name=a_prj_path.name,
        instrumentSerialNumber=serial_number,
        drive=drive_model,
        samples=sample_models,
    )
    return project


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


def samples_from_legacy_project(project: ZooscanProjectFolder) -> list[Sample]:
    # In a real implementation, you would fetch the samples from a database
    # For now, we'll return a mock list of samples
    samples = []
    for sample_name in project.zooscan_scan.list_samples_with_state():
        # Parse the sample name into components
        parsed_name = parse_sample_name(sample_name)

        # Create metadata from parsed components
        metadata = []
        for key, value in parsed_name.items():
            if key not in ["full_name", "components", "num_components"]:
                metadata.append(
                    {
                        "id": f"{sample_name}_{key}",
                        "name": key,
                        "value": str(value),
                        "description": f"Extracted from sample name: {key}",
                    }
                )

        # Create the sample with metadata
        samples.append(Sample(id=sample_name, name=sample_name, metadata=metadata))
    return samples
