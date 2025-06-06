import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from Models import (
    SubSample,
    SubSampleIn,
    LinkBackgroundReq,
    ScanToUrlReq,
    User,
    ScanPostRsp,
)
from auth import get_current_user_from_credentials
from helpers.web import raise_404, get_stream, raise_501
from img_proc.convert import convert_tiff_to_jpeg
from legacy.scans import find_scan_metadata, sub_scans_metadata_table_for_sample
from legacy.writers.scan import add_legacy_scan
from local_DB.data_utils import set_background_id
from local_DB.db_dependencies import get_db
from logger import logger
from modern.app_urls import is_download_url, extract_file_id_from_download_url
from modern.files import UPLOAD_DIR
from modern.from_legacy import (
    subsamples_from_legacy_project_and_sample,
    subsample_from_legacy,
    backgrounds_from_legacy_project,
)
from modern.ids import (
    scan_name_from_subsample_name,
    THE_SCAN_PER_SUBSAMPLE,
)
from modern.subsample import get_project_scans_metadata, add_subsample
from remote.DB import DB
from .utils import validate_path_components

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
    # Validate the project and sample hashes
    zoo_drive, zoo_project, sample_name, _ = validate_path_components(
        db, project_hash, sample_hash
    )

    logger.info(
        f"Getting subsamples for sample {sample_name} in project {zoo_project.name}"
    )

    # Get subsamples using the same structure as in subsamples_from_legacy_project_and_sample
    subsamples = subsamples_from_legacy_project_and_sample(db, zoo_project, sample_name)

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
    # Validate the project and sample hashes
    zoo_drive, zoo_project, sample_name, _ = validate_path_components(
        db, project_hash, sample_hash
    )

    logger.info(
        f"Creating subsample for sample {sample_name} in project {zoo_project.name}"
    )

    # The provided scan_id is not really OK, it's local TODO
    new_scan_id = add_subsample(db, zoo_project, sample_name, subsample)
    # Re-read from FS
    project_scans_metadata = get_project_scans_metadata(db, zoo_project)
    zoo_subsample_metadata = find_scan_metadata(
        project_scans_metadata, sample_name, new_scan_id
    )  # No concept of "subsample" in legacy
    assert zoo_subsample_metadata is not None, f"Subsample {subsample} was NOT created"
    ret = subsample_from_legacy(
        db, zoo_project, sample_name, subsample.name, zoo_subsample_metadata
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
    # Validate the project, sample, and subsample hashes
    zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )

    logger.info(
        f"Getting subsample {subsample_name} for sample {sample_name} in project {zoo_project.name}"
    )

    # Get the project scans metadata
    project_scans_metadata = get_project_scans_metadata(db, zoo_project)

    # Filter the metadata for the specific sample
    sample_scans_metadata = sub_scans_metadata_table_for_sample(
        project_scans_metadata, sample_name
    )

    # Find the metadata for the specific subsample
    scan_id = scan_name_from_subsample_name(subsample_name)
    zoo_metadata_sample = find_scan_metadata(
        sample_scans_metadata, sample_name, scan_id
    )

    if zoo_metadata_sample is None:
        raise_404(f"Subsample {subsample_name} not found in sample {sample_name}")
        assert False  # mypy

    subsample = subsample_from_legacy(
        db, zoo_project, sample_name, subsample_name, zoo_metadata_sample
    )

    return subsample


@router.delete("/{subsample_hash}")
def delete_subsample(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
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
    # Validate the project, sample, and subsample hashes
    zoo_drive, project_name, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )

    logger.info(
        f"Deleting subsample {subsample_name} for sample {sample_name} in project {project_name}"
    )

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to delete the subsample from the database
    # This is a placeholder - in a real implementation, you would delete the subsample from a database
    # For example: db_instance.delete(f"/projects/{project_hash}/samples/{sample_hash}/subsamples/{subsample_hash}")
    # For now, we'll just return a success message
    pass

    return {"message": f"Subsample {subsample_name} deleted successfully"}


@router.get("/{subsample_hash}/process")
def process_subsample(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> dict:
    """
    Process a specific subsample.

    Args:
        user: User from authentication.
        db: Database dependency.
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample.
        subsample_hash (str): The hash of the subsample to process.

    Returns:
        dict: A message indicating the subsample was processed.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    # Validate the project, sample, and subsample hashes
    zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )

    logger.info(
        f"Processing subsample {subsample_name} for sample {sample_name} in project {zoo_project.name}"
    )

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to process the subsample
    # This is a placeholder - in a real implementation, you would process the subsample
    # For example: result = db_instance.get(f"/projects/{project_hash}/samples/{sample_hash}/subsamples/{subsample_hash}/process")
    # For now, we'll just return a success message
    result = {
        "status": "success",
        "message": f"Subsample {subsample_name} processed successfully",
    }

    return result


@router.get("/{subsample_hash}/scan.jpg")
async def get_subsample_scan(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    # _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
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
    # Validate the project, sample, and subsample hashes
    zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )

    logger.info(
        f"Getting scan image for subsample {subsample_name} in sample {sample_name} in project {zoo_project.name}"
    )

    # Get the files for the subsample
    try:
        _subsample_files = zoo_project.zooscan_scan.work.get_files(
            subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
    except Exception as e:
        logger.error(f"Error getting files for subsample {subsample_name}: {str(e)}")
        raise_404(f"Scan image not found for subsample {subsample_name}")

    scan_file = zoo_project.zooscan_scan.get_8bit_file(
        subsample_name, THE_SCAN_PER_SUBSAMPLE
    )
    if not scan_file.exists():
        raise_404(f"Scan image not found for subsample {subsample_name}")

    # Convert the TIF file to JPG
    tmp_jpg = Path(tempfile.mktemp(suffix=".jpg"))
    convert_tiff_to_jpeg(scan_file, tmp_jpg)
    scan_file = tmp_jpg

    # Stream the file
    file_like, length, media_type = get_stream(scan_file)
    headers = {"content-length": str(length)}
    return StreamingResponse(file_like, headers=headers, media_type=media_type)


@router.post("/{subsample_hash}/scan_url")
def link_subsample_to_scan(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    scan_url: ScanToUrlReq,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> ScanPostRsp:
    # Validate the project, sample, and subsample hashes
    zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )
    logger.info(
        f"Received scan URL: {scan_url} for subsample {subsample_name} in sample {sample_name} in project {zoo_project.name}"
    )
    # In 'modern' world, the scan might be the first one for the subsample,
    # in which case the in-flight subsample becomes 'real' by materializing as files.
    # http://localhost:5000/download/upload_apero2023_tha_bioness_sup2000_017_st66_d_n1_d2_3_sur_4_raw_1.tif
    # Validate more
    if not is_download_url(scan_url.url):
        raise_501("Invalid scan URL, not produced here")
    src_image_path = UPLOAD_DIR / extract_file_id_from_download_url(scan_url.url)
    if not src_image_path.exists():
        raise_404(f"Scan URL {scan_url} not found")

    add_legacy_scan(db, zoo_project, scan_name_from_subsample_name(subsample_name))

    # Then we can work directly on legacy filesystem
    return ScanPostRsp(id=subsample_name + "XXXX", image="toto")


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
    # Validate the project, sample, and subsample hashes
    zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )

    logger.info(
        f"Getting image for subsample {subsample_name} for sample {sample_name} in project {zoo_project.name}"
    )

    # Validate that the background scan ID exists
    if not bg_to_ss.scanId:
        raise HTTPException(status_code=400, detail="Background scan ID is required")

    # Check if the background exists in the project
    backgrounds = backgrounds_from_legacy_project(zoo_project)
    background_ids = [bg.id for bg in backgrounds]

    if bg_to_ss.scanId not in background_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Background with ID {bg_to_ss.scanId} not found in project {zoo_project.name}",
        )

    set_background_id(
        db,
        zoo_drive.path.name,
        zoo_project.name,
        scan_name_from_subsample_name(subsample_name),
        bg_to_ss.scanId,
    )
    return bg_to_ss
