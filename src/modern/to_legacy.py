#
# Transformers from modern models to Legacy data
#
import shutil
import tempfile
from logging import Logger
from pathlib import Path
from typing import Optional, Dict, cast

import numpy as np

from ZooProcess_lib.img_tools import save_gif_image
from legacy.scans import ScanCSVLine


def reconstitute_fracid(fraction_id: str, fraction_id_suffix: Optional[str]) -> str:
    return fraction_id + ("_" + fraction_id_suffix if fraction_id_suffix else "")


def reconstitute_csv_line(scan_data: Dict) -> ScanCSVLine:
    ret = ScanCSVLine(**scan_data)  # type:ignore [typeddict-item]
    return cast(ScanCSVLine, ret)


def save_mask_image(logger: Logger, mask: np.ndarray, path: Path) -> None:
    tmp_path = tempfile.mktemp(suffix=".gif")
    logger.info(f"Saving mask image to {path}")
    save_gif_image(mask, Path(tmp_path))  # Write to a temp file
    shutil.move(tmp_path, path)  # Rename
