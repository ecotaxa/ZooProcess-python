# Process a scan from its vignettes until auto separation
import os
import time
from logging import Logger
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np

from ZooProcess_lib.LegacyMeta import Measurements
from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ROI import ROI, unique_visible_key
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from ZooProcess_lib.img_tools import get_creation_date
from helpers.paths import count_files_in_dir
from legacy.ids import measure_file_name
from modern.filesystem import ModernScanFileSystem
from modern.ids import THE_SCAN_PER_SUBSAMPLE, scan_name_from_subsample_name
from modern.tasks import Job
from providers.ImageList import ImageList
from providers.ML_multiple_classifier import (
    classify_all_images_from,
    ping_classify_server,
)
from providers.ML_multiple_separator import (
    separate_all_images_from,
    show_separations_in_images,
    ping_separator_server,
)


class VignettesToAutoSeparated(Job):

    def __init__(
        self, zoo_project: ZooscanProjectFolder, sample_name: str, subsample_name: str
    ):
        super().__init__((zoo_project, sample_name, subsample_name))
        # Params
        self.zoo_project = zoo_project
        self.sample_name = sample_name
        self.subsample_name = subsample_name
        # Derived
        self.scan_name = scan_name_from_subsample_name(subsample_name)
        # Modern side
        self.modern_fs = ModernScanFileSystem(zoo_project, sample_name, subsample_name)
        # Input
        self.cut_dir: Path = self.modern_fs.cut_dir
        # Output
        self.multiples_dir: Path = self.modern_fs.multiples_vis_dir
        self.scores_file: Path = self.modern_fs.scores_file_path

    def prepare(self):
        """
        Start the job execution.
        """
        self.logger = self._setup_job_logger(
            self.modern_fs.ensure_meta_dir() / "auto_sep_job.log"
        )
        # Log the start of the job execution
        self.logger.info(
            f"Starting automatic separation for project: {self.zoo_project.name}, sample: {self.sample_name}, subsample: {self.subsample_name}"
        )

        assert self.cut_dir.exists(), f"No thumbnails directory {self.cut_dir}"
        assert count_files_in_dir(self.cut_dir) > 0, f"No thumbnails in {self.cut_dir}"
        assert ping_classify_server(self.logger)[0], "Classify server is not responding"
        assert ping_separator_server(self.logger)[
            0
        ], f"Separator server is not responding"

    def run(self):
        self.logger.info(f"Determining multiples")
        # First ML step, send all images to the multiple classifier
        maybe_multiples, error = classify_all_images_from(
            self.logger, self.cut_dir, self.scores_file, 0.4
        )
        assert error is None, error

        self.logger.info(f"Separating multiples (auto)")
        # Second ML step, send potential multiples to the separator
        multiples_vis_dir = self.modern_fs.fresh_empty_multiples_vis_dir()
        image_list = ImageList(self.cut_dir, [m.name for m in maybe_multiples])
        # Send files by chunks to avoid the operator waiting too long with no feedback
        processed = 0
        to_process = len(image_list.get_images())
        start_time = time.time()
        for a_chunk in image_list.split(12):
            results, error = separate_all_images_from(self.logger, a_chunk)
            assert error is None, error
            assert results is not None  # mypy
            show_separations_in_images(self.cut_dir, results, multiples_vis_dir)
            processed += len(a_chunk.get_images())
            eta_str = self.compute_ETA(start_time, processed, to_process)
            self.logger.info(
                f"Processed {processed}/{to_process} images - ETA: {eta_str}"
            )

        # Add some marker that all went fine
        self.modern_fs.mark_ML_separation_done()

    @staticmethod
    def compute_ETA(start_time: float, processed: int, to_process: int) -> str:
        # Calculate ETA
        if processed > 0 and to_process > 0:
            elapsed_time = time.time() - start_time
            images_per_second = processed / elapsed_time
            remaining_images = to_process - processed
            eta_seconds = (
                remaining_images / images_per_second if images_per_second > 0 else 0
            )
            # Format ETA as minutes and seconds
            eta_minutes = int(eta_seconds // 60)
            eta_seconds_remainder = int(eta_seconds % 60)
            eta_str = f"{eta_minutes}m {eta_seconds_remainder}s"
        else:
            eta_str = "unknown"
        return eta_str

    def _cleanup_work(self):
        """Cleanup the files that the present process is going to (re) create"""
        # work_files = self.zoo_project.zooscan_scan.work.get_files(
        #     self.subsample_name, THE_SCAN_PER_SUBSAMPLE
        # )
        # if WRK_MSK1 in work_files:
        #     the_work_file = work_files[WRK_MSK1]
        #     assert isinstance(
        #         the_work_file, Path
        #     ), f"Unexpected {WRK_MSK1} (not a file?)!"
        #     os.remove(the_work_file)


def generate_box_measures(rois: List[ROI], scan_name: str, meta_file: Path) -> None:
    """Keep track of box measures, the vignettes names are indexes inside this list"""
    rows = []
    for a_roi in rois:
        bx, by = a_roi.x, a_roi.y
        height, width = a_roi.mask.shape
        rows.append(
            {
                "": unique_visible_key(a_roi),
                "Label": scan_name,
                "BX": bx,
                "BY": by,
                "Width": width,
                "Height": height,
            }
        )
    out = Measurements()
    out.header_row = ["", "Label", "BX", "BY", "Width", "Height"]
    out.data_rows = rows
    out.write(meta_file)


def get_scan_and_backgrounds(
    logger: Logger, zoo_project: ZooscanProjectFolder, subsample_name: str
) -> Tuple[Path, List[Path]]:
    # Get RAW scan file path, root of all dependencies
    raw_scan = zoo_project.zooscan_scan.raw.get_file(
        subsample_name, THE_SCAN_PER_SUBSAMPLE
    )
    assert raw_scan.exists(), f"No scan at {raw_scan}"
    raw_scan_date = get_creation_date(raw_scan)
    for_msg = raw_scan.relative_to(zoo_project.path)
    logger.info(f"Raw scan file {for_msg} dated {raw_scan_date}")
    zooscan_back = zoo_project.zooscan_back
    # We should have 2 RAW backgrounds
    # TODO: Use manual association, if relevant
    bg_raw_files = zooscan_back.get_last_raw_backgrounds_before(raw_scan_date)
    bg_scans = []
    for a_bg in bg_raw_files:
        assert (
            a_bg and a_bg.exists()
        ), f"Inconsistent in {zooscan_back.path} for {raw_scan_date}"
        bg_scan_date = get_creation_date(a_bg)
        for_msg = a_bg.relative_to(zoo_project.path)
        logger.info(f"Raw background file {for_msg} dated {bg_scan_date}")
        assert (
            bg_scan_date < raw_scan_date
        ), f"Background scan {for_msg} date is _after_ raw background date"
        bg_scans.append(a_bg)
    return raw_scan, bg_scans


def convert_scan_and_backgrounds(
    logger: Logger, processor: Processor, raw_scan: Path, bg_scans: List[Path]
):
    logger.info(f"Converting backgrounds")
    bg_converted_files = [
        processor.converter.do_file_to_image(a_raw_bg_file)
        for a_raw_bg_file in bg_scans
    ]
    logger.info(f"Combining backgrounds")
    combined_bg_image, bg_resolution = processor.bg_combiner.do_from_images(
        bg_converted_files
    )
    # Scan pre-processing
    logger.info(f"Converting scan")
    eight_bit_scan_image, scan_resolution = processor.converter.do_file_to_image(
        raw_scan
    )
    # Background removal
    logger.info(f"Removing background")
    scan_without_background = processor.bg_remover.do_from_images(
        combined_bg_image, bg_resolution, eight_bit_scan_image, scan_resolution
    )
    return scan_resolution, scan_without_background


def produce_cuts_and_index(
    logger: Logger,
    processor: Processor,
    thumbs_dir: Path,
    meta_dir: Optional[Path],
    image: np.ndarray,
    image_resolution: int,
    rois: List[ROI],
    scan_name: str,
) -> None:
    # Thumbnail generation
    logger.info(f"Extracting")
    logger.debug(f"Extracting to {thumbs_dir}")
    processor.extractor.extract_all_with_border_to_dir(
        image,
        image_resolution,
        rois,
        thumbs_dir,
        scan_name,
    )
    # Index generation
    if meta_dir is not None:
        os.makedirs(meta_dir, exist_ok=True)
        generate_box_measures(rois, scan_name, meta_dir / measure_file_name(scan_name))
