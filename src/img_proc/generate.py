from logging import Logger
from pathlib import Path

import cv2
import numpy as np

from ZooProcess_lib.LegacyMeta import Measurements
from ZooProcess_lib.img_tools import (
    load_image,
    borders_of_original,
    cropnp,
    save_gif_image,
)
from providers.ML_multiple_separator import RGB_RED_COLOR

EIGHT_BITS_WHITE = 255


def generate_separator_gif(
    logger: Logger,
    measures: Measurements,
    src_multiples_dir: Path,
    src_cut_dir: Path,
    mask_img_path: Path,
    dst_path: Path,
) -> None:
    # Sanity checks
    if not src_multiples_dir.is_dir():
        raise ValueError(
            f"Source image directory, with multiples, does not exist or is not a directory: {src_multiples_dir}"
        )

    if not mask_img_path.exists():
        raise ValueError(f"Mask image does not exist: {mask_img_path}")

    # Load mask
    logger.info(f"Loading mask image: {mask_img_path}")
    msk_img = load_image(mask_img_path, imread_mode=cv2.IMREAD_GRAYSCALE)

    # Create a blank image, 8bit grey levels, same size as template
    sep_img = np.zeros_like(msk_img)

    # Loop over multiples
    nb_multiples = 0
    for a_multiple_file in src_multiples_dir.iterdir():
        scan_img = load_image(
            src_cut_dir / a_multiple_file.name, imread_mode=cv2.IMREAD_GRAYSCALE
        )
        multiple_img = load_image(a_multiple_file, imread_mode=cv2.IMREAD_COLOR_RGB)
        assert (
            scan_img.shape[:2] == multiple_img.shape[:2]
        ), f"Inconsistent shapes b/w multiple and scan in {a_multiple_file.name}"
        line_for_image = measures.find(a_multiple_file.name[:-4])  # Remove final .png
        assert line_for_image is not None, f"No measure for {a_multiple_file.name}"
        top, left, bottom, right = borders_of_original(scan_img)
        scan_img_no_border = cropnp(
            scan_img, top=top, left=left, bottom=bottom, right=right
        )
        # Keep only red, i.e. user-drawn pixels, from multiple
        multiple_binary_img_no_border = cropnp(
            multiple_img, top=top, left=left, bottom=bottom, right=right
        )
        # Only separators drawn on objects (non-white) are kept, as the white of an image might
        # fall on another nearby object
        non_whites = np.all(scan_img_no_border != EIGHT_BITS_WHITE)
        multiple_binary_img_no_border[non_whites] = (
            0,
            0,
            0,
        )
        # Finally, paste into SEP global sheet
        meas_bx, meas_by, meas_width, meas_height = (
            int(line_for_image["BX"]),
            int(line_for_image["BY"]),
            int(line_for_image["Width"]),
            int(line_for_image["Height"]),
        )
        sep_sub_img = cropnp(
            sep_img,
            top=meas_by,
            left=meas_bx,
            bottom=meas_by + meas_height,
            right=meas_bx + meas_width,
        )
        # Check if each pixel's RGB values match RGB_RED_COLOR
        red_pixels = np.all(multiple_binary_img_no_border == RGB_RED_COLOR, axis=2)
        sep_sub_img[red_pixels] = EIGHT_BITS_WHITE
        nb_multiples += 1
    logger.info(f"Done for {nb_multiples} multiples of {mask_img_path}")
    save_gif_image(sep_img, dst_path)
    logger.info(f"Separator saved in {dst_path}")
