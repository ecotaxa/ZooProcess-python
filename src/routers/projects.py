import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from Models import Project, Background, Scan
from ZooProcess_lib.ZooscanFolder import ZooscanDrive
from auth import get_current_user_from_credentials
from config_rdr import config
from helpers.web import raise_404, get_stream
from img_proc.convert import convert_tiff_to_jpeg
from legacy.files import find_background_file
from legacy_to_remote.importe import import_old_project
from local_DB.db_dependencies import get_db
from logger import logger
from modern.from_legacy import (
    project_from_legacy,
    backgrounds_from_legacy_project,
    scans_from_legacy_project,
)
from remote.DB import DB
from .utils import validate_path_components

# Create a routers instance
router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


def list_all_projects(db: Session, drives_to_check: List[Path]) -> List[Project]:
    """
    List all projects from the specified drives.

    Args:
        db: Database session
        drives_to_check: Optional list of drive paths to check. If None, uses config.get_drives().

    Returns:
        List of Project objects.
    """
    # Create a list to store all projects
    all_projects = []
    # Iterate through each drive in the list
    for drive_path in drives_to_check:
        zoo_drive = ZooscanDrive(drive_path)
        for a_prj_path in zoo_drive.list():
            project = project_from_legacy(db, a_prj_path)
            all_projects.append(project)

    return all_projects


@router.get("")
def get_projects(
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> List[Project]:
    """
    Returns a list of subdirectories inside each element of DRIVES.

    This endpoint requires authentication using a JWT token obtained from the /login endpoint.
    """
    return list_all_projects(db, config.get_drives())


@router.get("/{project_hash}")
def get_project_by_hash(
    project_hash: str,
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> Project:
    """
    Returns a specific project identified by its hash.

    This endpoint requires authentication using a JWT token obtained from the /login endpoint.

    Args:
        project_hash: The hash of the project to retrieve.
    """
    # Validate the project hash and get the drive path and project folder
    zoo_drive, zoo_project, _, _ = validate_path_components(db, project_hash)
    project = project_from_legacy(db, zoo_project.path)
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
    project_hash: str,
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
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
    zoo_drive, zoo_project, _, _ = validate_path_components(db, project_hash)
    logger.info(f"Getting backgrounds for project {zoo_project.name}")
    return backgrounds_from_legacy_project(zoo_project)


@router.get("/{project_hash}/scans")
def get_scans(
    project_hash: str,
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> List[Scan]:
    """
    Get the list of scans associated with a project.

    Args:
        project_hash (str): The hash of the project to get scans for.
        _user: Security dependency to get the current user.
        db: Database dependency.

    Returns:
        List[Scan]: A list of scans associated with the project.

    Raises:
        HTTPException: If the project is not found or the user is not authorized.
    """
    zoo_drive, zoo_project, _, _ = validate_path_components(db, project_hash)
    logger.info(f"Getting scans for project {zoo_project.name}")

    return scans_from_legacy_project(db, zoo_project)


@router.get("/{project_hash}/background/{background_id}")
async def get_background(
    project_hash: str,
    background_id: str,
    # _user=Depends(get_current_user_from_credentials), # TODO: Fix on client side
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Get a specific background from a project by its ID.

    Args:
        project_hash (str): The hash of the project to get the background from.
        background_id (str): The ID of the background to retrieve from the project.
        _user: Security dependency to get the current user.

    Returns:
        Background: The requested background.

    Raises:
        HTTPException: If the project or background is not found
    """
    zoo_drive, zoo_project, _, _ = validate_path_components(db, project_hash)
    logger.info(f"Getting background {background_id} for project {zoo_project.name}")

    assert background_id.endswith(
        ".jpg"
    )  # This comes from @see:backgrounds_from_legacy_project
    background_name = background_id[:-4]

    background_file = find_background_file(zoo_project, background_name)
    if background_file is None:
        raise_404(
            f"Background with ID {background_id} not found in project {zoo_project.name}"
        )

    tmp_jpg = Path(tempfile.mktemp(suffix=".jpg"))
    convert_tiff_to_jpeg(background_file, tmp_jpg)
    file_like, length, media_type = get_stream(tmp_jpg)
    headers = {"content-length": str(length)}
    return StreamingResponse(file_like, headers=headers, media_type=media_type)
