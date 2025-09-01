import os
import tempfile
import time
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile, Depends
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from Models import VignetteResponse, VignetteData
from ZooProcess_lib.LegacyMeta import Measurements
from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ROI import ROI
from ZooProcess_lib.img_tools import (
    load_image,
    save_jpg_or_png_image,
    borders_of_original,
)
from helpers.logger import logger
from helpers.matrix import (
    save_matrix_as_gzip,
    is_valid_compressed_matrix,
    load_matrix_from_compressed,
)
from helpers.web import get_stream, raise_422, raise_500
from img_proc.drawing import apply_matrix_onto
from legacy.ids import measure_file_name
from local_DB.db_dependencies import get_db
from modern.filesystem import (
    ModernScanFileSystem,
    V10_THUMBS_TO_CHECK_SUBDIR,
    V10_THUMBS_SUBDIR,
)
from modern.ids import scan_name_from_subsample_name
from providers.ML_multiple_separator import BGR_RED_COLOR, RGB_RED_COLOR
from .utils import validate_path_components

# Constants
API_PATH_SEP = ":"
MSK_SUFFIX_TO_API = "_mask.gz"
MSK_SUFFIX_FROM_API = "_mask.png"
SEG_SUFFIX_FROM_API = "_seg.png"

router = APIRouter(
    tags=["vignettes"],
)


def processing_context(
    zoo_project=None, sample_name=None, subsample_name=None
) -> Tuple[Processor, Path, Path, Path]:
    """Get processing context for a subsample

    Args:
        zoo_project: ZooscanProjectFolder object representing the project
        sample_name: String representing the sample name
        subsample_name: String representing the subsample name

    Returns:
        Tuple containing:
            - processor: Processor object
            - thumbs_dir: Path to the thumbs directory
            - multiples_to_check_dir: Path to the multiples_to_check directory
            - meta_dir: Path to the v10 metadata directory
    """
    scan_name = scan_name_from_subsample_name(subsample_name)

    logger.info(f"{zoo_project}, {sample_name}, {subsample_name}, {scan_name}")
    processor = Processor.from_legacy_config(
        zoo_project.zooscan_config.read(),
        zoo_project.zooscan_config.read_lut(),
    )
    fs = ModernScanFileSystem(zoo_project, sample_name, subsample_name)
    return processor, fs.cut_dir, fs.multiples_vis_dir, fs.meta_dir


@router.get("/vignettes/{project_hash}/{sample_hash}/{subsample_hash}")
async def get_vignettes(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    only: Optional[str] = None,
    db: Session = Depends(get_db),
) -> VignetteResponse:
    """Get reference to the vignettes for a specific subsample.
    All vignettes are returned, either with an automatic separator drawn or not.

    Args:
        project_hash (str): The ID of the project
        sample_hash (str): The hash of the sample
        subsample_hash (str): The hash of the subsample
        only (str): Restrict output to this single image (by name)
        db (Session): Database session

    Returns:
        VignetteResponse: Response containing vignette data
    """
    # Validate the project, sample, and subsample hashes
    zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )
    processor, thumbs_dir, multiples_to_check_dir, _ = processing_context(
        zoo_project, sample_name, subsample_name
    )
    # Get multiples first
    assert multiples_to_check_dir is not None
    multiples_set = set(all_pngs_in_dir(multiples_to_check_dir))
    base_api_path = f"/{project_hash}/{sample_hash}/{subsample_hash}/"
    if only is None:
        # Get all vignettes
        assert thumbs_dir is not None
        all_vignettes = all_pngs_in_dir(thumbs_dir)
    else:
        # Focus on the requested one
        all_vignettes = [only]
    api_vignettes = []
    for a_vignette in sorted(all_vignettes):
        if a_vignette in multiples_set:
            # Segmenter
            sep_img_path = multiples_to_check_dir / a_vignette
            assert sep_img_path.is_file()
            _, rois = segment_mask(processor, sep_img_path)
            segmenter_output = []
            for i in range(len(rois)):
                seg_name = (
                    V10_THUMBS_TO_CHECK_SUBDIR
                    + API_PATH_SEP
                    + a_vignette
                    + f"_{i}{SEG_SUFFIX_FROM_API}"
                )
                segmenter_output.append(seg_name)
            matrix = (
                V10_THUMBS_TO_CHECK_SUBDIR
                + API_PATH_SEP
                + a_vignette
                + MSK_SUFFIX_TO_API
            )
            mask = V10_THUMBS_TO_CHECK_SUBDIR + API_PATH_SEP + a_vignette
        else:
            segmenter_output = []
            matrix = mask = None
        # Anti-cache measures
        if only is not None:
            stamp = "?t=" + str(time.time())
            if mask is not None:
                mask += stamp
            segmenter_output = [seg + stamp for seg in segmenter_output]
        vignette_data = VignetteData(
            scan=V10_THUMBS_SUBDIR + API_PATH_SEP + a_vignette,
            matrix=matrix,
            mask=mask,
            vignettes=segmenter_output,
        )
        api_vignettes.append(vignette_data)
    base_dir = "/api/backend/vignette" + base_api_path
    ret = VignetteResponse(data=api_vignettes, folder=base_dir)
    return ret


@router.get("/vignette/{project_hash}/{sample_hash}/{subsample_hash}/{img_path}")
async def get_vignette_image(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    img_path: str,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Get one vignette

    Args:
        project_hash (str): The hash of the project
        sample_hash (str): The hash of the sample
        subsample_hash (str): The hash of the subsample
        img_path (str): The path to the image
        db (Session): Database session

    Returns:
        StreamingResponse: The image as a streaming response
    """
    logger.info(
        f"get_a_vignette: {project_hash}/{sample_hash}/{subsample_hash}/{img_path}"
    )
    # Validate the project, sample, and subsample hashes
    zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )
    img_path = img_path.replace(API_PATH_SEP, "/")
    processor, thumbs_dir, multiples_to_check_dir, _ = processing_context(
        zoo_project, sample_name, subsample_name
    )
    assert processor.config is not None
    if img_path.endswith(SEG_SUFFIX_FROM_API):
        img_path = img_path[: -len(SEG_SUFFIX_FROM_API)]
        img_path, seg_num = img_path.rsplit("_", 1)
        multiple_name = img_path.rsplit("/", 1)[1]
        sep_img_path = multiples_to_check_dir / multiple_name
        assert sep_img_path.is_file(), f"Not a file: {sep_img_path}"
        sep_img, rois = segment_mask(processor, sep_img_path)
        vignette_in_vignette = processor.extractor.extract_image_at_ROI(
            sep_img, rois[int(seg_num)], erasing_background=True
        )
        tmp_png_path = Path(
            tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        )
        save_jpg_or_png_image(
            vignette_in_vignette, processor.config.resolution, tmp_png_path
        )
        img_file = Path(tmp_png_path)
    elif img_path.endswith(MSK_SUFFIX_TO_API):
        multiple_name = img_path[: -len(MSK_SUFFIX_TO_API)].rsplit("/", 1)[1]
        ret_img_path = multiples_to_check_dir / multiple_name
        temp_file = get_gzipped_matrix_from_mask(ret_img_path)
        img_file = Path(temp_file.name)
    else:
        multiple_name = img_path.rsplit("/", 1)[1]
        if img_path.startswith(V10_THUMBS_TO_CHECK_SUBDIR):
            img_file = multiples_to_check_dir / multiple_name
        elif img_path.startswith(V10_THUMBS_SUBDIR):
            img_file = thumbs_dir / multiple_name
        else:
            assert False, f"Unknown img_path: {img_path}"

    file_like, length, media_type = get_stream(img_file)
    # The naming is quite unpredictable as all could change, from raw scan
    # to segmentation and separation, so avoid caching on client side.
    # TODO: Dig more, this seems inefficient
    headers = {
        "content-length": str(length),
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return StreamingResponse(file_like, headers=headers, media_type=media_type)


def check_mask_sanity(
    scan_img: np.ndarray,
    mask: np.ndarray,
    subsample_name: str,
    img_basename: str,
    meta_dir: Path,
):
    """Ensure we are in sync with global image for future re-generation"""
    measure = Measurements().read(
        meta_dir / measure_file_name(scan_name_from_subsample_name(subsample_name))
    )
    line_for_image = measure.find(img_basename)
    if line_for_image is None:
        raise_500("Could not locate image from its mask")
        assert False
    top, left, bottom, right = borders_of_original(scan_img)
    height, width = bottom - top, right - left
    meas_width, meas_height = int(line_for_image["Width"]), int(
        line_for_image["Height"]
    )
    if meas_width != width or meas_height != height:
        raise_500(
            f"Mismatch between measures {meas_width}x{meas_height} and vignette {width}x{height}"
        )
    # # Clear the mask outside the boundaries
    # mask_height, mask_width = mask.shape[:2]
    # # Clear above top
    # if top > 0:
    #     mask[:top, :] = False
    # # Clear below bottom
    # if bottom < mask_height:
    #     mask[bottom:, :] = False
    # # Clear to the left of left
    # if left > 0:
    #     mask[:, :left] = False
    # # Clear to the right of right
    # if right < mask_width:
    #     mask[:, right:] = False


@router.post("/vignette_mask/{project_hash}/{sample_hash}/{subsample_hash}/{img_path}")
async def update_a_vignette_mask(
    project_hash: str,
    sample_hash: str,
    subsample_hash: str,
    img_path: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """Update a vignette using the drawn mask

    Args:
        project_hash (str): The ID of the project
        sample_hash (str): The hash of the sample
        subsample_hash (str): The hash of the subsample
        img_path (str): The path to the original image
        file (UploadFile): The uploaded file containing the mask
        db (Session): Database session

    Returns:
        dict: Status of the update operation
    """
    logger.info(
        f"update_a_vignette_mask: {project_hash}/{sample_hash}/{subsample_hash}/{img_path}"
    )
    # Validate the project, sample, and subsample hashes
    zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
        db, project_hash, sample_hash, subsample_hash
    )
    img_path = img_path.replace(API_PATH_SEP, "/")
    assert img_path.startswith(
        V10_THUMBS_SUBDIR
    )  # Convention with UI, ref is original image in cut directory
    assert img_path.endswith(".png")
    _, img_name = img_path.rsplit("/", 1)
    processor, thumbs_dir, multiples_to_check_dir, meta_dir = processing_context(
        zoo_project, sample_name, subsample_name
    )
    assert processor.config is not None
    # Read the content of the uploaded file
    content = await file.read()
    # Validate that the content is a gzip or zip-encoded matrix
    if not is_valid_compressed_matrix(content):
        raise_422("Invalid compressed matrix")
        assert False
    mask = load_matrix_from_compressed(content)
    scan_path = thumbs_dir / img_name
    scan_img = load_image(scan_path, cv2.IMREAD_GRAYSCALE)
    check_mask_sanity(scan_img, mask, subsample_name, img_name[:-4], meta_dir)
    scan_img_rgb = cv2.cvtColor(scan_img, cv2.COLOR_GRAY2RGB)
    masked_img = apply_matrix_onto(scan_img_rgb, mask)
    multiple_masked_path = multiples_to_check_dir / img_name
    # Save the file
    logger.info(f"Saving mask into {multiple_masked_path}")
    save_jpg_or_png_image(masked_img, processor.config.resolution, multiple_masked_path)

    return {
        "status": "success",
        "message": f"Image updated at {multiple_masked_path}",
        "image": str(img_name),
    }


def all_pngs_in_dir(a_dir: Path) -> List[str]:
    ret = []
    if a_dir is None:
        return ret
    for an_entry in os.scandir(a_dir):
        if not an_entry.is_file():
            continue
        if not an_entry.name.endswith(".png"):
            continue
        ret.append(an_entry.name)
    return ret


def segment_mask(
    processor: Processor, sep_img_path: Path
) -> Tuple[np.ndarray, List[ROI]]:
    sep_img = load_image(sep_img_path, cv2.IMREAD_COLOR_BGR)
    sep_img2 = cv2.extractChannel(sep_img, 1)
    sep_img2[sep_img[:, :, 2] == BGR_RED_COLOR[2]] = 255
    assert processor.config is not None
    rois, _ = processor.segmenter.find_ROIs_in_cropped_image(
        sep_img2, processor.config.resolution
    )
    return sep_img2, rois


def get_gzipped_matrix_from_mask(img_path):
    img_array = load_image(img_path, cv2.IMREAD_COLOR_RGB)
    # Create a binary image where pixels exactly match RGB_RED_COLOR
    binary_img = np.all(img_array == RGB_RED_COLOR, axis=2)
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png.gz")
    save_matrix_as_gzip(binary_img, temp_file.name)
    logger.info(f"saving matrix to temp file {temp_file.name}")
    temp_file.close()
    return temp_file
