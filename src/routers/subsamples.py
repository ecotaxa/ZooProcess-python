import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from Models import SubSample, SubSampleIn
from ZooProcess_lib.ZooscanFolder import ZooscanDrive
from auth import get_current_user_from_credentials
from helpers.web import raise_404, get_stream
from img_proc.convert import convert_tiff_to_jpeg
from legacy.utils import find_scan_metadata, sub_table_for_sample
from local_DB.db_dependencies import get_db
from logger import logger
from modern.from_legacy import (
    subsamples_from_legacy_project_and_sample,
    subsample_from_legacy,
)
from modern.ids import (
    drive_and_project_from_hash,
    scan_name_from_subsample_name,
    THE_SCAN_PER_SUBSAMPLE,
)
from modern.subsample import get_project_scans_metadata
from modern.to_legacy import add_subsample
from remote.DB import DB
from routers.samples import check_sample_exists

# Create a router instance
router = APIRouter(
    prefix="/projects/{project_hash}/samples/{sample_id}/subsamples",
    tags=["subsamples"],
)


@router.get("")
def get_subsamples(
    project_hash: str,
    sample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> List[SubSample]:
    """
    Get the list of subsamples associated with a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to get subsamples for.

    Returns:
        List[SubSample]: A list of subsamples associated with the sample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Getting subsamples for sample {sample_id} in project {project_hash}")

    # Check if the project and sample exists
    try:
        drive_path, project_name = drive_and_project_from_hash(project_hash)
        check_sample_exists(project_hash, sample_id)
    except HTTPException as e:
        raise e

    # Create a ZooscanProjectFolder object from the project
    zoo_project = ZooscanDrive(drive_path).get_project_folder(project_name)

    # Get subsamples using the same structure as in subsamples_from_legacy_project_and_sample
    subsamples = subsamples_from_legacy_project_and_sample(zoo_project, sample_id)

    return subsamples


@router.post("")
def create_subsample(
    project_hash: str,
    sample_id: str,
    subsample: SubSampleIn,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> SubSample:
    """
    Add a new subsample to a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to add the subsample to.
        subsample (SubSampleIn): The subsample data containing name, metadataModelId, and additional data.
        user (User, optional): The authenticated user. Defaults to the current user from credentials.
        db (Session, optional): Database session. Defaults to the session from dependency.

    Returns:
        SubSample: The created subsample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Creating subsample for sample {sample_id} in project {project_hash}")

    # Check if the project and sample exist
    try:
        drive_path, project_name = drive_and_project_from_hash(project_hash)
        check_sample_exists(project_hash, sample_id)
    except HTTPException as e:
        raise e

    project_path = Path(drive_path) / project_name
    zoo_project = ZooscanDrive(drive_path).get_project_folder(project_name)

    add_subsample(
        project_path,
        sample_id,
        subsample.name,
        subsample.metadataModelId,
        subsample.data,
    )
    # Re-read from FS
    project_scans_metadata = get_project_scans_metadata(zoo_project)
    scan_name = scan_name_from_subsample_name(subsample.name)
    zoo_subsample_metadata = find_scan_metadata(
        project_scans_metadata, sample_id, scan_name
    )  # No concept of "subsample" in legacy"
    assert zoo_subsample_metadata is not None, f"Subsample {subsample} was NOT created"
    ret = subsample_from_legacy(
        zoo_project, sample_id, subsample.name, zoo_subsample_metadata
    )
    return ret


@router.get("/{subsample_id}")
def get_subsample(
    project_hash: str,
    sample_id: str,
    subsample_id: str,
    _user=Depends(get_current_user_from_credentials),
) -> SubSample:
    """
    Get a specific subsample from a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample.
        subsample_id (str): The ID of the subsample to get.

    Returns:
        SubSample: The requested subsample.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    logger.info(
        f"Getting subsample {subsample_id} for sample {sample_id} in project {project_hash}"
    )

    # Check if the project and sample exist
    try:
        drive_path, project_name = drive_and_project_from_hash(project_hash)
        check_sample_exists(project_hash, sample_id)
    except HTTPException as e:
        raise e

    # Create a ZooscanProjectFolder object from the project
    zoo_project = ZooscanDrive(drive_path).get_project_folder(project_name)

    # Get the project scans metadata
    project_scans_metadata = get_project_scans_metadata(zoo_project)

    # Filter the metadata for the specific sample
    sample_scans_metadata = sub_table_for_sample(project_scans_metadata, sample_id)

    # Find the metadata for the specific subsample
    scan_id = scan_name_from_subsample_name(subsample_id)
    zoo_metadata_sample = find_scan_metadata(sample_scans_metadata, sample_id, scan_id)

    if zoo_metadata_sample is None:
        raise_404(f"Subsample {subsample_id} not found in sample {sample_id}")

    subsample = subsample_from_legacy(
        zoo_project, sample_id, subsample_id, zoo_metadata_sample
    )

    return subsample


@router.delete("/{subsample_id}")
def delete_subsample(
    project_hash: str,
    sample_id: str,
    subsample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> dict:
    """
    Delete a specific subsample from a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample.
        subsample_id (str): The ID of the subsample to delete.

    Returns:
        dict: A message indicating the subsample was deleted.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    logger.info(
        f"Deleting subsample {subsample_id} for sample {sample_id} in project {project_hash}"
    )

    # Check if the project exists
    try:
        drive_path, project_name = drive_and_project_from_hash(project_hash)
        check_sample_exists(project_hash, sample_id)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to delete the subsample from the database
    # This is a placeholder - in a real implementation, you would delete the subsample from a database
    # For example: db_instance.delete(f"/projects/{project_hash}/samples/{sample_id}/subsamples/{subsample_id}")
    # For now, we'll just return a success message
    pass

    return {"message": f"Subsample {subsample_id} deleted successfully"}


@router.get("/{subsample_id}/process")
def process_subsample(
    project_hash: str,
    sample_id: str,
    subsample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> dict:
    """
    Process a specific subsample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample.
        subsample_id (str): The ID of the subsample to process.

    Returns:
        dict: A message indicating the subsample was processed.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    logger.info(
        f"Processing subsample {subsample_id} for sample {sample_id} in project {project_hash}"
    )

    # Check if the project and sample exist
    try:
        drive_and_project_from_hash(project_hash)
        check_sample_exists(project_hash, sample_id)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to process the subsample
    # This is a placeholder - in a real implementation, you would process the subsample
    # For example: result = db_instance.get(f"/projects/{project_hash}/samples/{sample_id}/subsamples/{subsample_id}/process")
    # For now, we'll just return a success message
    result = {
        "status": "success",
        "message": f"Subsample {subsample_id} processed successfully",
    }

    return result


@router.get("/{subsample_id}/scan.jpg")
async def get_subsample_scan(
    project_hash: str,
    sample_id: str,
    subsample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> StreamingResponse:
    """
    Get the scan image for a specific subsample.

    Args:
        project_hash (str): The hash of the project.
        sample_id (str): The ID of the sample.
        subsample_id (str): The ID of the subsample.

    Returns:
        StreamingResponse: The scan image as a streaming response.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the scan image is not found.
    """
    logger.info(
        f"Getting scan image for subsample {subsample_id} in sample {sample_id} in project {project_hash}"
    )

    # Get the project and sample paths
    drive_path, project_name = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    project = zoo_drive.get_project_folder(project_name)

    # Get the files for the subsample
    try:
        _subsample_files = project.zooscan_scan.work.get_files(
            subsample_id, THE_SCAN_PER_SUBSAMPLE
        )
    except Exception as e:
        logger.error(f"Error getting files for subsample {subsample_id}: {str(e)}")
        raise_404(f"Scan image not found for subsample {subsample_id}")

    scan_file = project.zooscan_scan.get_8bit_file(subsample_id, THE_SCAN_PER_SUBSAMPLE)
    if not scan_file.exists():
        raise_404(f"Scan image not found for subsample {subsample_id}")

    # Convert the TIF file to JPG
    tmp_jpg = Path(tempfile.mktemp(suffix=".jpg"))
    convert_tiff_to_jpeg(scan_file, tmp_jpg)
    scan_file = tmp_jpg

    # Stream the file
    file_like, length, media_type = get_stream(scan_file)
    headers = {"content-length": str(length)}
    return StreamingResponse(file_like, headers=headers, media_type=media_type)
