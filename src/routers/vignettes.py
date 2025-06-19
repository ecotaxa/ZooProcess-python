import os
import tempfile
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile
from starlette.responses import StreamingResponse

from Models import VignetteResponse, VignetteData
from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ROI import ROI
from ZooProcess_lib.img_tools import load_image, save_lossless_small_image
from helpers.matrix import (
    save_matrix_as_gzip,
    is_valid_compressed_matrix,
    load_matrix_from_compressed,
)
from helpers.web import get_stream, raise_422
from img_proc.drawing import apply_matrix_onto
from modern.ids import THE_SCAN_PER_SUBSAMPLE
from modern.jobs.process import (
    LAST_PROCESS,
    V10_THUMBS_SUBDIR,
    V10_THUMBS_TO_CHECK_SUBDIR,
    V10_THUMBS_MULTIPLES_SUBDIR,
)
from providers.ML_multiple_separator import BGR_RED_COLOR, RGB_RED_COLOR
from logger import logger

# Constants
API_PATH_SEP = ":"
MSK_SUFFIX_TO_API = "_mask.gz"
MSK_SUFFIX_FROM_API = "_mask.png"
SEG_SUFFIX_FROM_API = "_seg.png"

router = APIRouter(
    tags=["vignettes"],
)


def processing_context() -> Tuple[Processor, Path, Path]:
    """TODO : Temporary until we have full path to subsample"""
    if LAST_PROCESS is None:
        raise Exception("No last process")
    zoo_project, sample_name, subsample_name, scan_name = LAST_PROCESS
    multiples_dir = (
        zoo_project.zooscan_scan.work.get_sub_directory(
            subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
        / V10_THUMBS_SUBDIR
        / V10_THUMBS_MULTIPLES_SUBDIR
    )
    multiples_to_check_dir = (
        zoo_project.zooscan_scan.work.get_sub_directory(
            subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
        / V10_THUMBS_SUBDIR
        / V10_THUMBS_TO_CHECK_SUBDIR
    )
    logger.info(f"{zoo_project}, {sample_name}, {subsample_name}, {scan_name}")
    processor = Processor.from_legacy_config(
        zoo_project.zooscan_config.read(),
        zoo_project.zooscan_config.read_lut(),
    )
    return processor, multiples_dir, multiples_to_check_dir


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


@router.get("/vignettes")
async def get_vignettes() -> VignetteResponse:
    """Get some vignettes"""
    processor, multiples_dir, multiples_to_check_dir = processing_context()
    assert multiples_to_check_dir is not None
    multiples = all_pngs_in_dir(multiples_to_check_dir)
    api_vignettes = []
    for a_multiple in multiples:
        # Segmenter
        sep_img_path = multiples_to_check_dir / a_multiple
        assert sep_img_path.is_file()
        _, rois = segment_mask(processor, sep_img_path)
        segmenter_output = []
        for i in range(len(rois)):
            seg_name = (
                V10_THUMBS_MULTIPLES_SUBDIR
                + API_PATH_SEP
                + a_multiple
                + f"_{i}{SEG_SUFFIX_FROM_API}"
            )
            segmenter_output.append(seg_name)
        vignette_data = VignetteData(
            scan=V10_THUMBS_MULTIPLES_SUBDIR + API_PATH_SEP + a_multiple,
            matrix=V10_THUMBS_TO_CHECK_SUBDIR
            + API_PATH_SEP
            + a_multiple
            + MSK_SUFFIX_TO_API,
            mask=V10_THUMBS_TO_CHECK_SUBDIR + API_PATH_SEP + a_multiple,
            vignettes=segmenter_output,
        )
        api_vignettes.append(vignette_data)
    base_dir = "/api/backend/vignette"
    ret = VignetteResponse(data=api_vignettes, folder=base_dir)
    return ret


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


@router.get("/vignette/{img_path}")
async def get_a_vignette(img_path: str) -> StreamingResponse:
    """Get one vignette"""
    logger.info(f"get_a_vignette: {img_path}")
    img_path = img_path.replace(API_PATH_SEP, "/")
    processor, multiples_dir, multiples_to_check_dir = processing_context()
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
        save_lossless_small_image(
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
        elif img_path.startswith(V10_THUMBS_MULTIPLES_SUBDIR):
            img_file = multiples_dir / multiple_name
        else:
            assert False, f"Unknown img_path: {img_path}"

    file_like, length, media_type = get_stream(img_file)
    # The naming is quite unpredictable as all could change, from raw scan
    # to segmentation and separation, so avoid caching on client side.
    headers = {
        "content-length": str(length),
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    return StreamingResponse(file_like, headers=headers, media_type=media_type)


@router.post("/vignette_mask/{img_path}")
async def update_a_vignette_mask(img_path: str, file: UploadFile = File(...)) -> dict:
    """Update a vignette using the drawn mask"""
    logger.info(f"update_a_vignette_mask: {img_path}")
    img_path = img_path.replace(API_PATH_SEP, "/")
    assert img_path.startswith(V10_THUMBS_TO_CHECK_SUBDIR)  # Convention with UI
    assert img_path.endswith(MSK_SUFFIX_TO_API)
    img_path = img_path[: -len(MSK_SUFFIX_TO_API)]
    img_name = img_path.rsplit("/", 1)[1]
    processor, multiples_dir, multiples_to_check_dir = processing_context()
    assert processor.config is not None
    # Read the content of the uploaded file
    content = await file.read()
    # Validate that the content is a gzip or zip-encoded matrix
    if not is_valid_compressed_matrix(content):
        raise_422("Invalid compressed matrix")
        assert False
    mask = load_matrix_from_compressed(content)
    multiple_path = multiples_dir / img_name
    multiple_img = load_image(multiple_path, cv2.IMREAD_COLOR_RGB)
    masked_img = apply_matrix_onto(multiple_img, mask)
    multiple_masked_path = multiples_to_check_dir / img_name
    # Save the file
    logger.info(f"Saving mask into {multiple_masked_path}")
    save_lossless_small_image(
        masked_img, processor.config.resolution, multiple_masked_path
    )

    return {
        "status": "success",
        "message": f"Image updated at {multiple_masked_path}",
        "image": str(img_name),
    }
