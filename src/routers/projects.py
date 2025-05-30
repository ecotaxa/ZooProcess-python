from fastapi import APIRouter, Depends, HTTPException
from typing import List
import tempfile
from pathlib import Path

from fastapi.responses import StreamingResponse
from Models import Project, Drive, Background, Scan
from auth import get_current_user_from_credentials
from ZooProcess_lib.ZooscanFolder import ZooscanDrive
from modern.ids import drive_and_project_from_hash
from modern.from_legacy import (
    project_from_legacy,
    backgrounds_from_legacy_project,
    scans_from_legacy_project,
)
from legacy_to_remote.importe import import_old_project
from legacy.files import find_background_file
from helpers.web import raise_404, get_stream
from img_proc.convert import convert_tiff_to_jpeg
from remote.DB import DB
from logger import logger
from config_rdr import config

# Create a routers instance
router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


def list_all_projects(drives_to_check: List[Path]):
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
    # Iterate through each drive in the list
    for drive in drives_to_check:
        zoo_drive = ZooscanDrive(drive)
        for a_prj_path in zoo_drive.list():
            project = project_from_legacy(a_prj_path)
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
    return list_all_projects(config.DRIVES)


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
    drive_path, project_name = drive_and_project_from_hash(project_hash)
    project_path = Path(drive_path) / project_name
    project = project_from_legacy(project_path)
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


@router.get("/{project_hash}/backgrounds")
def get_backgrounds(
    project_hash: str, user=Depends(get_current_user_from_credentials)
) -> List[Background]:
    """
    Get the list of backgrounds associated with a project.

    Args:
        project_hash (str): The hash of the project to get backgrounds for.
        user: Security dependency to get the current user.

    Returns:
        List[Background]: A list of backgrounds associated with the project.

    Raises:
        HTTPException: If the project is not found or the user is not authorized.
    """
    logger.info(f"Getting backgrounds for project {project_hash}")

    drive_path, project_name = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    project = zoo_drive.get_project_folder(project_name)
    return backgrounds_from_legacy_project(project)


@router.get("/{project_hash}/scans")
def get_scans(
    project_hash: str,
    # user=Depends(get_current_user_from_credentials)
) -> List[Scan]:
    """
    Get the list of scans associated with a project.

    Args:
        project_hash (str): The hash of the project to get scans for.
        user: Security dependency to get the current user.

    Returns:
        List[Scan]: A list of scans associated with the project.

    Raises:
        HTTPException: If the project is not found or the user is not authorized.
    """
    logger.info(f"Getting scans for project {project_hash}")

    drive_path, project_name = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    project = zoo_drive.get_project_folder(project_name)

    return scans_from_legacy_project(project)


@router.get("/{project_hash}/background/{background_id}")
async def get_background(
    project_hash: str,
    background_id: str,
    # user=Depends(get_current_user_from_credentials), # TODO: Should be protected?
) -> StreamingResponse:
    """
    Get a specific background from a project by its ID.

    Args:
        project_hash (str): The hash of the project to get the background from.
        background_id (str): The ID of the background to retrieve from the project.
        user: Security dependency to get the current user.

    Returns:
        Background: The requested background.

    Raises:
        HTTPException: If the project or background is not found
    """
    logger.info(f"Getting background {background_id} for project {project_hash}")

    drive_path, project_name = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    project = zoo_drive.get_project_folder(project_name)

    assert background_id.endswith(
        ".jpg"
    )  # This comes from @see:backgrounds_from_legacy_project
    background_name = background_id[:-4]

    background_file = find_background_file(project, background_name)
    if background_file is None:
        raise_404(
            f"Background with ID {background_id} not found in project {project_hash}"
        )

    tmp_jpg = Path(tempfile.mktemp(suffix=".jpg"))
    convert_tiff_to_jpeg(background_file, tmp_jpg)
    file_like, length, media_type = get_stream(tmp_jpg)
    headers = {"content-length": str(length)}
    return StreamingResponse(file_like, headers=headers, media_type=media_type)
