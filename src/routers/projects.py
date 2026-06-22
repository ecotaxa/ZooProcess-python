import json
import os
import tempfile
from pathlib import Path
from typing import List, cast, Dict

import cv2
import numpy as np
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from Models import Project, Background, Scan, ScanStats, ScanStatsDetail, ScanDetailEnum
from ZooProcess_lib.ZooscanFolder import ZooscanDrive
from ZooProcess_lib.img_tools import load_image
from config_rdr import config
from helpers.auth import get_current_user_from_credentials
from helpers.logger import logger
from helpers.web import raise_404, get_stream
from img_proc.convert import convert_tiff_to_jpeg
from legacy.backgrounds import find_final_background_file, find_raw_background_file
from legacy_to_remote.importe import import_old_project
from local_DB.db_dependencies import get_db
from modern.filesystem import TOP_V10_DIR, ModernScanFileSystem
from modern.from_legacy import (
    project_from_legacy,
    backgrounds_from_legacy_project,
    scans_from_legacy_project,
    DEPTH_ALL,
)
from modern.ids import subsample_name_from_scan_name
from modern.jobs import MIN_SCORE, BIG_IMAGE_THRESHOLD
from providers.ImageList import ImageList
from providers.ML_multiple_separator import (
    BGR_RED_COLOR,
    separate_all_images_from,
)
from remote.DB import DB
from .utils import validate_path_components

# Create a routers instance
router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


def list_all_projects(
    db: Session, drives_to_check: List[Path], depth: int
) -> List[Project]:
    """
    List all projects from the specified drives.

    Args:
        db: Database session
        drives_to_check: List of drive paths to check.

    Returns:
        List of Project objects.
    """
    # Create a list to store all projects
    all_projects = []
    # Iterate through each drive in the list
    for drive_path in drives_to_check:
        zoo_drive = ZooscanDrive(drive_path)
        for a_prj_path in zoo_drive.list():
            try:
                project = project_from_legacy(db, a_prj_path, depth)
            except FileNotFoundError:
                # Looks like e.g. /zooscan/Zooscan_ptb_jb_2024_sn001/ is incomplete
                continue
            all_projects.append(project)

    return all_projects


@router.get("")
def get_projects(
    depth: int = DEPTH_ALL,
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> List[Project]:
    """
    Returns a list of subdirectories inside each element of DRIVES.

    This endpoint requires authentication using a JWT token obtained from the /login endpoint.
    """
    return list_all_projects(db, config.get_drives(), depth)


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


@router.get("/{project_hash}/stats")
def get_project_scanning_stats(
    project_hash: str,
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> List[ScanStats]:
    zoo_drive, zoo_project, _, _ = validate_path_components(db, project_hash)

    result: List[ScanStats] = []

    def files_in_dir(path: Path) -> List[Path]:
        return [a_file for a_file in path.iterdir() if a_file.is_file()]

    def is_after(path: Path, path_cmp: Path) -> bool:
        return path.stat().st_mtime > path_cmp.stat().st_mtime

    def has_a_separator(image_path: Path) -> bool:
        sep_img = load_image(image_path, cv2.IMREAD_COLOR_BGR)
        return cast(bool, np.any(np.all(sep_img == BGR_RED_COLOR, axis=2)))

    v10_work_dir: Path = zoo_project.zooscan_scan.path / TOP_V10_DIR
    if not v10_work_dir.exists():
        return result
    for scan_dir in v10_work_dir.iterdir():
        subsample = subsample_name_from_scan_name(scan_dir.name)
        modern_fs = ModernScanFileSystem(zoo_project, "", subsample)
        # We need output directories...
        nb_subdirs = 1 if modern_fs.cut_dir.exists() else 0
        nb_subdirs += 1 if modern_fs.multiples_vis_dir.exists() else 0
        if nb_subdirs != 2:
            continue
        # ...and the flag indicating that manual separation is finished
        if not modern_fs.SEP_validated_file_path.exists():
            continue

        # Stats for what happened before ML separation
        after_seg = len(files_in_dir(modern_fs.cut_dir))
        with open(modern_fs.scores_file_path, "r") as f:
            scores: Dict[str, float] = json.load(f)
        sent_to_ml_separator = {k: v for k, v in scores.items() if v > MIN_SCORE}

        # Big images were filtered but forced into this directory
        sep_images_list = ImageList(modern_fs.multiples_vis_dir)
        zip_path = sep_images_list.zipped(logger)  # Just to store sizes
        os.unlink(zip_path)
        big_ones = {
            f
            for (f, sz) in sep_images_list.size_by_name.items()
            if sz >= BIG_IMAGE_THRESHOLD
        }
        for big in big_ones:
            try:
                del sent_to_ml_separator[big]
            except KeyError:
                pass

        # Separation work directory. Written into by ML or user
        in_sep_dir = files_in_dir(modern_fs.multiples_vis_dir)

        # Writes which happened after the end of the separation job -> user modifications
        auto_sep_log = modern_fs.ensure_meta_dir() / "auto_sep_job.log"
        modified_images = [f for f in in_sep_dir if is_after(f, auto_sep_log)]
        modified_images_names = [f.name for f in modified_images]
        unmodified_images = [f for f in in_sep_dir if not is_after(f, auto_sep_log)]
        unmodified_images_names = [f.name for f in unmodified_images]

        # Images added by user but the ML separator did not even see them
        added_by_user = set(modified_images_names).difference(
            sent_to_ml_separator.keys()
        )
        # Keep only the ones with separators
        created_by_user = {
            f for f in added_by_user if has_a_separator(modern_fs.multiples_vis_dir / f)
        }

        to_separate = modified_images_names.copy()
        for added in added_by_user:
            to_separate.remove(added)
        # Re-separate original images
        to_separate_list = ImageList(modern_fs.cut_dir, to_separate)
        results, error = separate_all_images_from(logger, to_separate_list)
        assert error is None, error
        assert results is not None
        predictions = results.predictions
        modified_by_user = set()
        cleared_by_user = set()
        for a_prediction in predictions:
            coords = a_prediction.separation_coordinates
            ml_separated = len(coords[0]) != 0
            user_separated = has_a_separator(
                modern_fs.multiples_vis_dir / a_prediction.name
            )
            if ml_separated:
                if user_separated:
                    modified_by_user.add(a_prediction.name)
                else:
                    cleared_by_user.add(a_prediction.name)
            else:
                if user_separated:
                    created_by_user.add(a_prediction.name)
                else:
                    # Ignored: ML found no sep and the user did not fix
                    pass

        details: List[ScanStatsDetail] = []
        for qualif, state in zip(
            [
                unmodified_images_names,
                created_by_user,
                modified_by_user,
                cleared_by_user,
            ],
            [
                ScanDetailEnum.untouched,
                ScanDetailEnum.created,
                ScanDetailEnum.modified,
                ScanDetailEnum.cleared,
            ],
        ):
            details.extend(
                [
                    ScanStatsDetail(image=f, score=scores.get(f, -1), state=state)
                    for f in qualif
                ]
            )
        details.sort(key=lambda x: x.image, reverse=True)
        stats_for_scan = ScanStats(
            name=subsample,
            segmented=after_seg,
            tooBig=len(big_ones),
            sentToSeparator=len(sent_to_ml_separator),
            untouchedByUser=len(unmodified_images),
            createdByUser=len(created_by_user),
            modifiedByUser=len(modified_by_user),
            clearedByUser=len(cleared_by_user),
            details=details,
        )
        result.append(stats_for_scan)

    return result


@router.get("/{project_hash}/background/{background_id}")
async def get_image_for_background(
    project_hash: str,
    background_id: str,
    # _user=Depends(get_current_user_from_credentials), # TODO: Fix on client side
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Get JPG equivalent of a specific background from a project by its ID.

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
    bg_date, bg_type = background_name.rsplit(
        "_", 1
    )  # e.g. 20201009_1412_fnl or _bg1 or _bg2

    if bg_type == "fnl":
        background_file = find_final_background_file(zoo_project, bg_date)
    else:
        background_file = find_raw_background_file(zoo_project, bg_date, bg_type[-1])
    if background_file is None:
        raise_404(
            f"Background with ID {background_id} not found in project {zoo_project.name}"
        )

    tmp_jpg = Path(tempfile.mktemp(suffix=".jpg"))
    convert_tiff_to_jpeg(background_file, tmp_jpg)
    file_like, length, media_type = get_stream(tmp_jpg)
    headers = {"content-length": str(length)}
    return StreamingResponse(file_like, headers=headers, media_type=media_type)
