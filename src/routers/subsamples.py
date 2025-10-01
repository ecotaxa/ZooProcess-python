import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from Models import (
    SubSample,
    SubSampleIn,
    LinkBackgroundReq,
    ScanPostRsp,
    ProcessRsp,
    MarkSubsampleReq,
    SubSampleStateEnum,
    User,
    ScanToUrlReq,
)
from ZooProcess_lib.Processor import Processor
from helpers.auth import (
    get_current_user_from_credentials,
    get_ecotaxa_token_from_credentials,
)
from helpers.logger import logger
from helpers.web import raise_404, get_stream, raise_422, raise_500
from img_proc.convert import convert_image_for_display
from legacy.ids import raw_file_name
from legacy.scans import find_scan_metadata, sub_scans_metadata_table_for_sample
from legacy.writers.scan import add_legacy_scan
from local_DB.data_utils import set_background_id
from local_DB.db_dependencies import get_db
from modern.app_urls import (
    is_download_url,
    extract_file_id_from_download_url,
    SCAN_JPEG,
)
from modern.files import UPLOAD_DIR
from modern.filesystem import ModernScanFileSystem
from modern.from_legacy import (
    subsamples_from_legacy_project_and_sample,
    subsample_from_legacy,
    backgrounds_from_legacy_project,
)
from modern.from_modern import modern_subsample_state
from modern.ids import (
    scan_name_from_subsample_name,
    THE_SCAN_PER_SUBSAMPLE,
)
from modern.jobs.FreshScanToVignettes import FreshScanToVignettes
from modern.jobs.VerifiedSepToUpload import VerifiedSeparationToEcoTaxa
from modern.jobs.VignettesToAutoSep import VignettesToAutoSeparated
from modern.subsample import get_project_scans_metadata, add_subsample
from modern.tasks import JobScheduler, Job
from modern.utils import job_to_task_rsp
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

    zoo_scan_metadata_for_sample = _sample_scans_meta(
        zoo_project, sample_name, subsample_name, db
    )

    if zoo_scan_metadata_for_sample is None:
        raise_404(f"Subsample {subsample_name} not found in sample {sample_name}")
        assert False  # mypy

    subsample = subsample_from_legacy(
        db, zoo_project, sample_name, subsample_name, zoo_scan_metadata_for_sample
    )

    return subsample


def _sample_scans_meta(zoo_project, sample_name, subsample_name, db):
    # Get the project scans metadata
    project_scans_metadata = get_project_scans_metadata(db, zoo_project)
    # Filter the metadata for the specific sample
    sample_scans_metadata = sub_scans_metadata_table_for_sample(
        project_scans_metadata, sample_name
    )
    # Find the metadata for the specific subsample
    scan_id = scan_name_from_subsample_name(subsample_name)
    zoo_scan_metadata_for_sample = find_scan_metadata(
        sample_scans_metadata, sample_name, scan_id
    )
    return zoo_scan_metadata_for_sample


@router.delete("/{subsample_hash}")
def delete_subsample(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete specific subsample. So far we just delete (some) v10 data.

    Args:
        user: Security dependency to get the current user.
        db: Database dependency.
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample.
        subsample_hash (str): The hash of the subsample to delete the MSK for.

    Returns:
        dict: A message indicating the MSK file deletion result.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    # Validate the project, sample, and subsample hashes
    _zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )
    modern_fs = ModernScanFileSystem(zoo_project, sample_name, subsample_name)
    state = modern_subsample_state(zoo_project, sample_name, subsample_name, modern_fs)

    message = "nothing to do"
    match state:
        case SubSampleStateEnum.SEGMENTATION_FAILED:
            result = remove_MSK(modern_fs, sample_name, subsample_name)
            message = f"MSK file for subsample {subsample_name} {result}"
        case SubSampleStateEnum.MULTIPLES_GENERATION_FAILED:
            result = remove_multiples_dir(modern_fs, sample_name, subsample_name)
            message = f"Thumbs directory for subsample {subsample_name} {result}"
        case SubSampleStateEnum.UPLOAD_FAILED:
            result = remove_upload_zip(modern_fs, sample_name, subsample_name)
            message = f"Zip for subsample {subsample_name} {result}"
        case SubSampleStateEnum.UPLOADED:
            result = remove_upload_zip(modern_fs, sample_name, subsample_name)
            message = f"Zip for subsample {subsample_name} {result}"

    return {"message": message}


def remove_multiples_dir(
    modern_fs: ModernScanFileSystem, sample_name: str, subsample_name: str
) -> str:
    to_erase = modern_fs.multiples_vis_dir
    try:
        if to_erase.exists():
            shutil.rmtree(to_erase)
            logger.info(
                f"Deleted thumbs directory for subsample {subsample_name} in sample {sample_name}: {to_erase}"
            )
            result = "deleted"
        else:
            logger.info(
                f"No thumbs directory found to delete for subsample {subsample_name} in sample {sample_name}: {to_erase}"
            )
            result = "not_found"
    except Exception as e:
        logger.error(
            f"Error deleting thumbs directory for subsample {subsample_name} in sample {sample_name}: {e}"
        )
        result = "?"
        raise_500(str(e))
    return result


def remove_MSK(
    modern_fs: ModernScanFileSystem, sample_name: str, subsample_name: str
) -> str:
    msk_path = modern_fs.MSK_file_path
    try:
        if msk_path.exists():
            msk_path.unlink()
            logger.info(
                f"Deleted MSK file for subsample {subsample_name} in sample {sample_name}: {msk_path}"
            )
            result = "deleted"
        else:
            logger.info(
                f"No MSK file found to delete for subsample {subsample_name} in sample {sample_name}: {msk_path}"
            )
            result = "not_found"
    except Exception as e:
        logger.error(
            f"Error deleting MSK file for subsample {subsample_name} in sample {sample_name}: {e}"
        )
        result = "?"
        raise_500(str(e))
    return result


def remove_upload_zip(
    modern_fs: ModernScanFileSystem, sample_name: str, subsample_name: str
) -> str:
    upload_zip_path = modern_fs.zip_for_upload
    try:
        if upload_zip_path.exists():
            upload_zip_path.unlink()
            logger.info(
                f"Deleted ZIP file for subsample {subsample_name} in sample {sample_name}: {upload_zip_path}"
            )
            result = "deleted"
        else:
            logger.info(
                f"No ZIP file found to delete for subsample {subsample_name} in sample {sample_name}: {upload_zip_path}"
            )
            result = "not_found"
    except Exception as e:
        logger.error(
            f"Error deleting ZIP file for subsample {subsample_name} in sample {sample_name}: {e}"
        )
        result = "?"
        raise_500(str(e))
    return result


@router.post("/{subsample_hash}/process")
def process_subsample(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    _user=Depends(get_current_user_from_credentials),
    ecotaxa_token: str = Depends(get_ecotaxa_token_from_credentials),
    db: Session = Depends(get_db),
) -> ProcessRsp:
    """
    Process a specific subsample. Returns a task ID if needed to process the subsample.

    Args:
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample.
        subsample_hash (str): The hash of the subsample to process.
        _user: User from authentication.
        db: Database dependency.

    Returns:
        ProcessRsp: A capsule around the job which does/did the processing.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    # Validate the project, sample, and subsample hashes
    zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )
    modern_fs = ModernScanFileSystem(zoo_project, sample_name, subsample_name)
    state = modern_subsample_state(zoo_project, sample_name, subsample_name, modern_fs)
    to_launch: Job | None = None
    # noinspection PyTypeChecker
    job_state: Callable[[Job], bool] = Job.will_do
    match state:
        case SubSampleStateEnum.ACQUIRED | SubSampleStateEnum.SEGMENTATION_FAILED:
            to_launch = FreshScanToVignettes(zoo_project, sample_name, subsample_name)
            if state == SubSampleStateEnum.SEGMENTATION_FAILED:
                # noinspection PyTypeChecker
                job_state = Job.is_in_error
        case (
            SubSampleStateEnum.MSK_APPROVED
            | SubSampleStateEnum.MULTIPLES_GENERATION_FAILED
        ):
            to_launch = VignettesToAutoSeparated(
                zoo_project, sample_name, subsample_name
            )
            if state == SubSampleStateEnum.MULTIPLES_GENERATION_FAILED:
                # noinspection PyTypeChecker
                job_state = Job.is_in_error
        case (
            SubSampleStateEnum.SEPARATION_VALIDATION_DONE
            | SubSampleStateEnum.UPLOAD_FAILED
        ):
            to_launch = VerifiedSeparationToEcoTaxa(
                zoo_project, sample_name, subsample_name, ecotaxa_token
            )
            if state == SubSampleStateEnum.UPLOAD_FAILED:
                # noinspection PyTypeChecker
                job_state = Job.is_in_error

    ret: Job | None = None
    if to_launch is not None:
        with JobScheduler.jobs_lock:
            there_tasks = JobScheduler.find_jobs_like(to_launch, job_state)
            if len(there_tasks) == 0:
                JobScheduler.submit(to_launch)
                ret = to_launch
            else:
                ret = there_tasks[-1]
    return ProcessRsp(task=job_to_task_rsp(ret))


@router.post("/{subsample_hash}/mark")
def mark_subsample(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    marking_data: MarkSubsampleReq,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> SubSample:
    """
    Mark that the subsample is validated by a user.

    Args:
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample.
        subsample_hash (str): The hash of the subsample to process.
        marking_data (MarkSubsampleReq): The validation data including status, comments, and optional validation date.
        user: User from authentication.
        db: Database dependency.

    Returns:
        The updated SubSample

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    # Validate the project, sample, and subsample hashes
    zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )

    # Use current datetime if not provided
    validation_date = marking_data.validation_date or datetime.now()
    modern_fs = ModernScanFileSystem(zoo_project, sample_name, subsample_name)

    state = modern_subsample_state(zoo_project, sample_name, subsample_name, modern_fs)
    match state:
        case SubSampleStateEnum.SEGMENTED if marking_data.status == "approved":
            modern_fs.mark_MSK_validated(validation_date)
        case SubSampleStateEnum.MULTIPLES_GENERATED if (
            marking_data.status == "separated"
        ):
            modern_fs.mark_SEP_validated(validation_date)

    # Log the validation action
    logger.info(
        f"Marking subsample {subsample_name} as {marking_data.status} by user {user.name} with comments: {marking_data.comments}"
    )

    subsample = subsample_from_legacy(
        db,
        zoo_project,
        sample_name,
        subsample_name,
        _sample_scans_meta(zoo_project, sample_name, subsample_name, db),
    )
    return subsample


@router.get("/{subsample_hash}/{img_name}")
async def get_subsample_scan(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    img_name: str,
    # _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Get the scan image for a specific subsample.

    Args:
        project_hash (str): The hash of the project.
        sample_hash (str): The hash of the sample.
        subsample_hash (str): The hash of the subsample.
        img_name (str): The name of the image to return.
            "scan.jpg" magic file is the RAW scan converted for display.
            Others are for browsing the _work folder, which might not exists outside archived projects.

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
    work_path = zoo_project.zooscan_scan.work.path
    if work_path.exists():
        subsample_files = zoo_project.zooscan_scan.work.get_files(
            subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
    else:
        subsample_files = dict()

    if img_name == SCAN_JPEG:
        real_file = zoo_project.zooscan_scan.get_8bit_file(
            subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
        if not real_file.exists():
            processor = Processor.from_legacy_config(
                zoo_project.zooscan_config.read(),
                zoo_project.zooscan_config.read_lut(),
            )
            raw_sample_file = zoo_project.zooscan_scan.raw.get_file(
                subsample_name, THE_SCAN_PER_SUBSAMPLE
            )
            processor.converter.do_file_to_file(raw_sample_file, real_file, False)
    else:
        real_files: List[Path] = list(
            filter(
                lambda p: isinstance(p, Path) and p.name == img_name,  # type:ignore
                subsample_files.values(),
            )
        )
        if not real_files:
            raise_404(f"Image {img_name} not found for subsample {subsample_name}")
        real_file = real_files[0]
    returned_file = convert_image_for_display(real_file)

    # Stream the file
    file_like, length, media_type = get_stream(returned_file)
    headers = {"content-length": str(length)}
    return StreamingResponse(file_like, headers=headers, media_type=media_type)


@router.get("/{subsample_hash}/v10/{img_name}")
async def get_subsample_modern_scan(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    img_name: str,
    # _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Get the v10 scan image for a specific subsample.

    Args:
        project_hash (str): The hash of the project.
        sample_hash (str): The hash of the sample.
        subsample_hash (str): The hash of the subsample.
        img_name (str): The name of the image to return.

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
        f"Getting modern scan image {img_name} for subsample {subsample_name} in sample {sample_name} in project {zoo_project.name}"
    )
    modern_fs = ModernScanFileSystem(zoo_project, sample_name, subsample_name)
    real_files: List[Path] = list(
        filter(
            lambda p: p.name == img_name,
            modern_fs.meta_dir.iterdir(),
        )
    )
    if not real_files:
        raise_404(
            f"Image {img_name} not found for modern side of subsample {subsample_name}"
        )
    real_file = real_files[0]
    returned_file = convert_image_for_display(real_file)

    # Stream the file
    file_like, length, media_type = get_stream(returned_file)
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
        raise_422("Invalid scan URL, not produced here")
    src_image_path = UPLOAD_DIR / extract_file_id_from_download_url(scan_url.url)
    if not src_image_path.exists():
        raise_404(f"Scan URL {scan_url} not found")
    if not src_image_path.is_file():
        raise_422("Invalid scan URL, not a file")
    if not src_image_path.suffix.lower() == ".tif":
        raise_422("Invalid scan URL, not a .tif file")

    scan_name = scan_name_from_subsample_name(subsample_name)
    # TODO: Log a bit, we're _writing_ into legacy
    add_legacy_scan(db, zoo_project, scan_name)
    work_dir = zoo_project.zooscan_scan.work.path / scan_name
    if not work_dir.exists():
        logger.info(f"Creating work directory {work_dir}")
        work_dir.mkdir()
    dst_path = zoo_project.zooscan_scan.raw.path / raw_file_name(scan_name)
    logger.info(f"Copying tif to {dst_path}")
    shutil.copy(src_image_path, dst_path)

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
    Link a scan to its background. The background is identified by a MongoDB ID.

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
