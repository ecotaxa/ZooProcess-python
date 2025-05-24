from pathlib import Path
from typing import Tuple

from fastapi import HTTPException

from Models import Drive
from legacy.drives import get_drive_path


def hash_from_drive_and_project(drive_model: Drive, a_prj_path: Path):
    """
    Compute some user and browser compatible IDs for URLs
    """
    url_hash = f"{drive_model.name}|{a_prj_path.name}"
    return url_hash


def drive_and_project_from_hash(project_hash: str) -> Tuple[Path, str, Path]:
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
    return drive_path, project_name, project_path
