from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pathlib import Path

from Models import Project, Drive
from auth import get_current_user_from_credentials
from ZooProcess_lib.ZooscanFolder import ZooscanDrive
from modern.ids import drive_and_project_from_hash
from modern.from_legacy import project_from_legacy
from legacy_to_remote.importe import import_old_project
from remote.DB import DB
from logger import logger
from config_rdr import config

# Create a routers instance
router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


def list_all_projects(drives_to_check=None):
    """
    List all projects from the specified drives.

    Args:
        drives_to_check: Optional list of drive paths to check. If None, uses config.DRIVES.
        serial_number: Optional serial number to use for projects. Default is "PROD123".

    Returns:
        List of Project objects.
    """
    # Create a list to store all projects
    all_projects = []
    # Use provided drives or default to config.DRIVES
    if drives_to_check is None:
        drives_to_check = config.DRIVES
    # Iterate through each drive in the list
    for drive_path in drives_to_check:
        drive = Path(drive_path)
        drive_model = Drive(id=drive.name, name=drive.name, url=drive_path)
        drive_zoo = ZooscanDrive(drive_path)

        for a_prj_path in drive_zoo.list():
            project = project_from_legacy(drive_model, a_prj_path)
            all_projects.append(project)

    return all_projects


@router.get("")
def get_projects(
    user=Depends(get_current_user_from_credentials),
) -> List[Project]:
    """
    Returns a list of subdirectories inside each element of DRIVES.

    This endpoint requires authentication using a JWT token obtained from the /login endpoint.
    """
    return list_all_projects()


@router.get("/{project_hash}")
def get_project_by_hash(
    project_hash: str,
    user=Depends(get_current_user_from_credentials),
) -> Project:
    """
    Returns a specific project identified by its hash.

    This endpoint requires authentication using a JWT token obtained from the /login endpoint.

    Args:
        project_hash: The hash of the project to retrieve.
    """
    # Get the specific project by hash
    drive_path, project_name, project_path = drive_and_project_from_hash(project_hash)
    drive_model = Drive(id=drive_path.name, name=drive_path.name, url=str(drive_path))
    project = project_from_legacy(drive_model, project_path)
    return project


@router.post("/import")
def import_project(project: Project):
    """
    Imports a project.
    """
    json = import_old_project(project)
    return json


@router.get("/test")
def test(project: Project):
    """
    Temporary API to test the import of a project
    try to link background and subsamples
    try because old project have not information about the links
    links appear only when scan are processed
    then need to parse
    """

    logger.info("test")
    logger.info(f"project: {project}")

    db = DB(bearer=project.bearer, db=project.db)

    return {"status": "success", "message": "Test endpoint"}
