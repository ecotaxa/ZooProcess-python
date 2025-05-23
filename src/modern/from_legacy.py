#
# Transformers from Legacy data to modern models
#
import re
from pathlib import Path

from Models import Project, Drive


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

    project = Project(
        path=str(a_prj_path),
        id=unq_id,
        name=a_prj_path.name,
        instrumentSerialNumber=serial_number,
        drive=drive_model,
    )
    return project
