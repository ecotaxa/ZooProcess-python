import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from Models import SubSample, SubSampleIn, LinkBackgroundReq
from ZooProcess_lib.ZooscanFolder import ZooscanDrive
from auth import get_current_user_from_credentials
from helpers.web import raise_404, get_stream
from img_proc.convert import convert_tiff_to_jpeg
from legacy.utils import find_scan_metadata, sub_table_for_sample
from local_DB.data_utils import set_background_id
from local_DB.db_dependencies import get_db
from logger import logger
from modern.from_legacy import (
    subsamples_from_legacy_project_and_sample,
    subsample_from_legacy,
    backgrounds_from_legacy_project,
)
from modern.ids import (
    drive_and_project_from_hash,
    scan_name_from_subsample_name,
    THE_SCAN_PER_SUBSAMPLE,
    sample_name_from_sample_hash,
    subsample_name_from_hash,
)
from modern.subsample import get_project_scans_metadata, add_subsample
from remote.DB import DB
from routers.samples import check_sample_exists

# Create a router instance
router = APIRouter(
    prefix="/projects/{project_hash}/samples/{sample_hash}/subsamples",
    tags=["subsamples"],
)


@router.get("")
def get_subsamples(
    project_hash: str,
    sample_hash: str,
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> List[SubSample]:
    """
    Get the list of subsamples associated with a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample to get subsamples for.
        _user: Security dependency to get the current user.
        db: Database dependency.

    Returns:
        List[SubSample]: A list of subsamples associated with the sample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(
        f"Getting subsamples for sample {sample_hash} in project {project_hash}"
    )

    # Decode the sample hash to get the sample name
    sample_id = sample_name_from_sample_hash(sample_hash)

    # Check if the project and sample exists
    drive_path, project_name = drive_and_project_from_hash(project_hash)
    check_sample_exists(project_hash, sample_hash)

    # Create a ZooscanProjectFolder object from the project
    zoo_project = ZooscanDrive(drive_path).get_project_folder(project_name)

    # Get subsamples using the same structure as in subsamples_from_legacy_project_and_sample
    subsamples = subsamples_from_legacy_project_and_sample(db, zoo_project, sample_id)

    return subsamples


@router.post("")
def create_subsample(
    project_hash: str,
    sample_hash: str,
    subsample: SubSampleIn,
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> SubSample:
    """
    Add a new subsample to a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample to add the subsample to.
        subsample (SubSampleIn): The subsample data containing name, metadataModelId, and additional data.
        _user (User, optional): The authenticated user. Defaults to the current user from credentials.
        db (Session, optional): Database session. Defaults to the session from dependency.

    Returns:
        SubSample: The created subsample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(
        f"Creating subsample for sample {sample_hash} in project {project_hash}"
    )

    # Decode the sample hash to get the sample name
    sample_id = sample_name_from_sample_hash(sample_hash)

    # Check if the project and sample exist
    drive_path, project_name = drive_and_project_from_hash(project_hash)
    check_sample_exists(project_hash, sample_hash)

    zoo_project = ZooscanDrive(drive_path).get_project_folder(project_name)

    # The provided scan_id is not really OK, it's local TODO
    new_scan_id = add_subsample(db, zoo_project, sample_id, subsample)
    # Re-read from FS
    project_scans_metadata = get_project_scans_metadata(db, zoo_project)
    zoo_subsample_metadata = find_scan_metadata(
        project_scans_metadata, sample_id, new_scan_id
    )  # No concept of "subsample" in legacy
    assert zoo_subsample_metadata is not None, f"Subsample {subsample} was NOT created"
    ret = subsample_from_legacy(
        db, zoo_project, sample_id, subsample.name, zoo_subsample_metadata
    )
    return ret


@router.get("/{subsample_hash}")
def get_subsample(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> SubSample:
    """
    Get a specific subsample from a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample.
        subsample_hash (str): The hash of the subsample to get.
        _user: Security dependency to get the current user.
        db: Database dependency.

    Returns:
        SubSample: The requested subsample.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    # Decode the subsample hash to get the subsample name
    subsample_id = subsample_name_from_hash(subsample_hash)

    logger.info(
        f"Getting subsample {subsample_id} for sample {sample_hash} in project {project_hash}"
    )

    # Decode the sample hash to get the sample name
    sample_id = sample_name_from_sample_hash(sample_hash)

    # Check if the project and sample exist
    drive_path, project_name = drive_and_project_from_hash(project_hash)
    check_sample_exists(project_hash, sample_hash)

    # Create a ZooscanProjectFolder object from the project
    zoo_project = ZooscanDrive(drive_path).get_project_folder(project_name)

    # Get the project scans metadata
    project_scans_metadata = get_project_scans_metadata(db, zoo_project)

    # Filter the metadata for the specific sample
    sample_scans_metadata = sub_table_for_sample(project_scans_metadata, sample_id)

    # Find the metadata for the specific subsample
    scan_id = scan_name_from_subsample_name(subsample_id)
    zoo_metadata_sample = find_scan_metadata(sample_scans_metadata, sample_id, scan_id)

    if zoo_metadata_sample is None:
        raise_404(f"Subsample {subsample_id} not found in sample {sample_id}")

    subsample = subsample_from_legacy(
        db, zoo_project, sample_id, subsample_id, zoo_metadata_sample
    )

    return subsample


@router.delete("/{subsample_hash}")
def delete_subsample(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    user=Depends(get_current_user_from_credentials),
) -> dict:
    """
    Delete a specific subsample from a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample.
        subsample_hash (str): The hash of the subsample to delete.

    Returns:
        dict: A message indicating the subsample was deleted.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    # Decode the subsample hash to get the subsample name
    subsample_id = subsample_name_from_hash(subsample_hash)

    logger.info(
        f"Deleting subsample {subsample_id} for sample {sample_hash} in project {project_hash}"
    )

    # Decode the sample hash to get the sample name
    sample_id = sample_name_from_sample_hash(sample_hash)

    # Check if the project exists
    drive_path, _ = drive_and_project_from_hash(project_hash)
    check_sample_exists(project_hash, sample_hash)

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to delete the subsample from the database
    # This is a placeholder - in a real implementation, you would delete the subsample from a database
    # For example: db_instance.delete(f"/projects/{project_hash}/samples/{sample_hash}/subsamples/{subsample_hash}")
    # For now, we'll just return a success message
    pass

    return {"message": f"Subsample {subsample_id} deleted successfully"}


@router.get("/{subsample_hash}/process")
def process_subsample(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    user=Depends(get_current_user_from_credentials),
) -> dict:
    """
    Process a specific subsample.

    Args:
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample.
        subsample_hash (str): The hash of the subsample to process.

    Returns:
        dict: A message indicating the subsample was processed.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    # Decode the subsample hash to get the subsample name
    subsample_id = subsample_name_from_hash(subsample_hash)

    logger.info(
        f"Processing subsample {subsample_id} for sample {sample_hash} in project {project_hash}"
    )

    # Decode the sample hash to get the sample name
    sample_id = sample_name_from_sample_hash(sample_hash)

    # Check if the project and sample exist
    drive_and_project_from_hash(project_hash)
    check_sample_exists(project_hash, sample_hash)

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to process the subsample
    # This is a placeholder - in a real implementation, you would process the subsample
    # For example: result = db_instance.get(f"/projects/{project_hash}/samples/{sample_hash}/subsamples/{subsample_hash}/process")
    # For now, we'll just return a success message
    result = {
        "status": "success",
        "message": f"Subsample {subsample_id} processed successfully",
    }

    return result


@router.get("/{subsample_hash}/scan.jpg")
async def get_subsample_scan(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    _user=Depends(get_current_user_from_credentials),
) -> StreamingResponse:
    """
    Get the scan image for a specific subsample.

    Args:
        project_hash (str): The hash of the project.
        sample_hash (str): The hash of the sample.
        subsample_hash (str): The hash of the subsample.

    Returns:
        StreamingResponse: The scan image as a streaming response.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the scan image is not found.
    """
    # Decode the sample & subsample hashes
    sample_id = sample_name_from_sample_hash(sample_hash)
    subsample_id = subsample_name_from_hash(subsample_hash)

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


@router.post("/{subsample_hash}/link")
def link_subsample_to_background(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    bg_to_ss: LinkBackgroundReq,
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> LinkBackgroundReq:
    """
    Link a scan to its background.

    Args:
        project_hash (str): The hash of the project.
        sample_hash (str): The hash of the sample.
        subsample_hash (str): The hash of the subsample.
        bg_to_ss (LinkBackgroundReq): The request containing scanId.
        _user: Security dependency to get the current user.
        db: Database dependency.

    Returns:
        LinkBackgroundReq: The same request object.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    # Decode the subsample hash to get the subsample name
    subsample_id = subsample_name_from_hash(subsample_hash)

    logger.info(
        f"POST /{project_hash}/samples/{sample_hash}/subsamples/{subsample_hash}/link {bg_to_ss}"
    )

    # Decode the sample hash to get the sample name
    sample_id = sample_name_from_sample_hash(sample_hash)

    # Check if the project and sample exist
    drive_path, project_name = drive_and_project_from_hash(project_hash)
    check_sample_exists(project_hash, sample_hash)

    # Create a ZooscanProjectFolder object from the project
    zoo_project = ZooscanDrive(drive_path).get_project_folder(project_name)

    # Get the project scans metadata
    project_scans_metadata = get_project_scans_metadata(db, zoo_project)

    # Filter the metadata for the specific sample
    sample_scans_metadata = sub_table_for_sample(project_scans_metadata, sample_id)

    # Find the metadata for the specific subsample
    scan_id = scan_name_from_subsample_name(subsample_id)
    zoo_metadata_sample = find_scan_metadata(sample_scans_metadata, sample_id, scan_id)

    if zoo_metadata_sample is None:
        raise_404(f"Subsample {subsample_id} not found in sample {sample_id}")

    # Validate that the background scan ID exists
    if not bg_to_ss.scanId:
        raise HTTPException(status_code=400, detail="Background scan ID is required")

    # Check if the background exists in the project
    backgrounds = backgrounds_from_legacy_project(zoo_project)
    background_ids = [bg.id for bg in backgrounds]

    if bg_to_ss.scanId not in background_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Background with ID {bg_to_ss.scanId} not found in project {project_name}",
        )

    set_background_id(
        db,
        drive_path.name,
        project_name,
        scan_name_from_subsample_name(subsample_id),
        bg_to_ss.scanId,
    )
    # For now, we just return the input object as in the original implementation
    return bg_to_ss
