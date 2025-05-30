from pathlib import Path
from typing import Tuple

from fastapi import HTTPException

from Models import Drive
from legacy.drives import get_drive_path


def hash_from_project(a_prj_path: Path):
    """
    Compute some user and browser compatible IDs for URLs
    Assumes that the drive's name is _always_ the project parent directory name
    """
    drive_name = a_prj_path.parent.name
    url_hash = f"{drive_name}|{a_prj_path.name}"
    return url_hash


def drive_and_project_from_hash(project_hash: str) -> Tuple[Path, str]:
    """
    Extract drive and project names from a project hash generated above.
    """
    try:
        drive_name, project_name = project_hash.split("|")
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid project ID format: {project_hash}. Expected format: drive|project",
        )

    drive_path = get_drive_path(drive_name)
    if drive_path is None:
        raise HTTPException(
            status_code=404, detail=f"Project with ID {project_hash} not found"
        )
    project_path = Path(drive_path) / project_name
    if not (project_path.exists() and project_path.is_dir()):
        raise HTTPException(
            status_code=404, detail=f"Project with ID {project_hash} not found"
        )
    return drive_path, project_name


THE_SCAN_PER_SUBSAMPLE = 1


def subsample_name_from_scan_name(scan_name: str):
    """
    Extract subsample name from scan name by removing trailing "_1" if present.

    Args:
        scan_name (str): The scan name

    Returns:
        str: The subsample name
    """
    if scan_name.endswith(f"_{THE_SCAN_PER_SUBSAMPLE}"):
        return scan_name[:-2]
    return scan_name


def scan_name_from_subsample_name(subsample_name: str):
    """
    Create scan name from subsample name by adding trailing "_1".
    This is the reverse function of subsample_name_from_scan_name.

    Args:
        subsample_name (str): The subsample name

    Returns:
        str: The scan name
    """
    return f"{subsample_name}_{THE_SCAN_PER_SUBSAMPLE}"
