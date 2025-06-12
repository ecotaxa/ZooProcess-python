#
# Transformers from modern models to Legacy data
#
import os
from logging import Logger
from typing import Optional, Dict, cast

import numpy as np

from ZooProcess_lib.ZooscanFolder import ZooscanScanWorkFolder, MSK1_ENDING
from ZooProcess_lib.img_tools import save_gif_image
from legacy.scans import ScanCSVLine
from modern.ids import THE_SCAN_PER_SUBSAMPLE, scan_name_from_subsample_name


def reconstitute_fracid(fraction_id: str, fraction_id_suffix: Optional[str]) -> str:
    return fraction_id + ("_" + fraction_id_suffix if fraction_id_suffix else "")


def reconstitute_csv_line(scan_data: Dict) -> ScanCSVLine:
    ret = ScanCSVLine(**scan_data)  # type:ignore [typeddict-item]
    return cast(ScanCSVLine, ret)


def save_mask_image(
    logger: Logger, mask: np.ndarray, work: ZooscanScanWorkFolder, subsample_name: str
) -> None:
    gif_dir = work.get_sub_directory(subsample_name, THE_SCAN_PER_SUBSAMPLE)
    gif_name = scan_name_from_subsample_name(subsample_name) + MSK1_ENDING
    gif_path = gif_dir.joinpath(gif_name)
    gif_work_path = gif_dir.joinpath(gif_name + ".tmp")
    logger.info(f"Saving mask image to {gif_path}")
    save_gif_image(mask, gif_work_path)  # Write to a temp file
    os.rename(gif_work_path, gif_path)  # Rename
