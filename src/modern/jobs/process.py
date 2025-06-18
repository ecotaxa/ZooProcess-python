# Process a scan from its background until segmentation
import os
import pickle
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

from config_rdr import config
from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder, WRK_MSK1
from ZooProcess_lib.img_tools import get_creation_date
from modern.ids import THE_SCAN_PER_SUBSAMPLE, scan_name_from_subsample_name
from modern.tasks import Job
from modern.to_legacy import save_mask_image
from providers.ML_multiple_classifier import classify_all_images_from
from providers.ML_multiple_separator import (
    separate_all_images_from,
    show_separations_in_images,
)
from providers.utils import ImageList

V10_THUMBS_SUBDIR = "v10_thumbs"
V10_THUMBS_MULTIPLES_SUBDIR = "multiples"
V10_THUMBS_TO_CHECK_SUBDIR = "multiples_vis"

# Yuk, for ensuring it works
LAST_PROCESS: Optional[Tuple[ZooscanProjectFolder, str, str, str]] = None


def _get_last_process_path() -> Path:
    """Get the path to the LAST_PROCESS pickle file."""
    logs_dir = Path(config.WORKING_DIR) / "logs"
    logs_dir.mkdir(exist_ok=True, parents=True)
    return logs_dir / "last_process.pkl"


def save_last_process():
    """Save LAST_PROCESS to a pickle file."""
    global LAST_PROCESS
    if LAST_PROCESS is None:
        return

    try:
        with open(_get_last_process_path(), "wb") as f:
            pickle.dump(LAST_PROCESS, f)
    except (pickle.PickleError, IOError) as e:
        print(f"Error saving LAST_PROCESS: {e}")


def load_last_process():
    """Load LAST_PROCESS from a pickle file if it exists."""
    global LAST_PROCESS
    path = _get_last_process_path()
    if path.exists():
        try:
            with open(path, "rb") as f:
                LAST_PROCESS = pickle.load(f)
        except (pickle.PickleError, IOError) as e:
            print(f"Error loading LAST_PROCESS: {e}")


# Load LAST_PROCESS at module initialization
load_last_process()


class BackgroundAndScanToSegmented(Job):

    def __init__(
        self, zoo_project: ZooscanProjectFolder, sample_name: str, subsample_name: str
    ):
        super().__init__()
        self.zoo_project = zoo_project
        self.sample_name = sample_name
        self.subsample_name = subsample_name
        self.scan_name = scan_name_from_subsample_name(subsample_name)
        global LAST_PROCESS
        LAST_PROCESS = (zoo_project, sample_name, subsample_name, self.scan_name)
        save_last_process()
        # Image inputs
        self.raw_scan: Path = Path("xyz")  # Just to keep mypy happy
        self.bg_scans: List[Path] = []

    def prepare(self):
        """
        Start the job execution.
        Pre-requisites:
            - 2 RAW backgrounds
            - 1 RAW scan
        Process a scan from its background until first segmentation.
        """
        prj_path = self.zoo_project.path
        # Mark the job as started
        self.mark_started()

        # Log the start of the job execution
        self.logger.info(
            f"Starting processing for project: {self.zoo_project.name}, sample: {self.sample_name}, subsample: {self.subsample_name}"
        )

        # Get RAW scan file path, root of all dependencies
        raw_scan = self.zoo_project.zooscan_scan.raw.get_file(
            self.subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
        assert raw_scan.exists()
        raw_scan_date = get_creation_date(raw_scan)
        for_msg = raw_scan.relative_to(prj_path)
        self.logger.info(f"Raw scan file {for_msg} dated {raw_scan_date}")
        self.raw_scan = raw_scan

        zooscan_back = self.zoo_project.zooscan_back
        # We should have 2 RAW backgrounds
        # TODO: Use manual association, if relevant
        bg_raw_files = zooscan_back.get_last_raw_backgrounds_before(raw_scan_date)
        for a_bg in bg_raw_files:
            assert a_bg.exists()
            bg_scan_date = get_creation_date(a_bg)
            for_msg = a_bg.relative_to(prj_path)
            self.logger.info(f"Raw background file {for_msg} dated {bg_scan_date}")
            assert (
                bg_scan_date < raw_scan_date
            ), f"Background scan {for_msg} date is _after_ raw background date"
            self.bg_scans.append(a_bg)

    def run(self):
        self._cleanup_work()
        processor = Processor.from_legacy_config(
            self.zoo_project.zooscan_config.read(),
            self.zoo_project.zooscan_config.read_lut(),
        )
        self.logger.info(f"Converting backgrounds")
        bg_converted_files = [
            processor.converter.do_file_to_image(a_raw_bg_file)
            for a_raw_bg_file in self.bg_scans
        ]
        self.logger.info(f"Combining backgrounds")
        combined_bg_image, bg_resolution = processor.bg_combiner.do_from_images(
            bg_converted_files
        )

        # Scan pre-processing
        self.logger.info(f"Converting scan")
        eight_bit_scan_image, scan_resolution = processor.converter.do_file_to_image(
            self.raw_scan
        )

        # Background removal
        self.logger.info(f"Removing background")
        scan_without_background = processor.bg_remover.do_from_images(
            combined_bg_image, bg_resolution, eight_bit_scan_image, scan_resolution
        )

        # Mask generation
        self.logger.info(f"Generating MSK")
        mask = processor.segmenter.get_mask_from_image(scan_without_background)
        save_mask_image(
            self.logger, mask, self.zoo_project.zooscan_scan.work, self.subsample_name
        )

        # Segmentation
        self.logger.info(f"Segmenting")
        rois, stats = processor.segmenter.find_ROIs_in_image(
            scan_without_background,
            scan_resolution,
        )
        self.logger.info(f"Segmentation stats: {stats}")

        # Thumbnail generation
        self.logger.info(f"Extracting")
        thumbs_dir = (
            self.zoo_project.zooscan_scan.work.get_sub_directory(
                self.subsample_name, THE_SCAN_PER_SUBSAMPLE
            )
            / V10_THUMBS_SUBDIR
        )
        os.makedirs(thumbs_dir, exist_ok=True)
        processor.extractor.extract_all_with_border_to_dir(
            scan_without_background,
            scan_resolution,
            rois,
            thumbs_dir,
            self.scan_name,
        )

        self.logger.info(f"Determining multiples")
        # Create an empty 'v10_thumbs/multiples' subdirectory
        multiples_dir = thumbs_dir / V10_THUMBS_MULTIPLES_SUBDIR
        if multiples_dir.exists():
            shutil.rmtree(multiples_dir)
        multiples_dir.mkdir(parents=False)
        _, error = classify_all_images_from(self.logger, thumbs_dir, 0.4, multiples_dir)
        assert error is None, error

        self.logger.info(f"Separating multiples (auto)")
        # Create an empty 'v10_thumbs/multiples_vis' subdirectory
        multiples_vis_dir = thumbs_dir / V10_THUMBS_TO_CHECK_SUBDIR
        if multiples_vis_dir.exists():
            shutil.rmtree(multiples_vis_dir)
        multiples_vis_dir.mkdir(parents=False)
        image_list = ImageList(multiples_dir)
        # Send files by chunks to avoid the operator waiting too long with no feedback
        processed = 0
        to_process = len(image_list.get_images())
        for a_chunk in image_list.split(12):
            results, error = separate_all_images_from(self.logger, a_chunk)
            assert error is None, error
            assert results is not None  # mypy
            show_separations_in_images(multiples_dir, results, multiples_vis_dir)
            processed += len(a_chunk.get_images())
            self.logger.info(f"Processed {processed}/{to_process} images")

    def _cleanup_work(self):
        """Cleanup the files that present process is going to (re) create"""
        work_files = self.zoo_project.zooscan_scan.work.get_files(
            self.subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
        if WRK_MSK1 in work_files:
            the_work_file = work_files[WRK_MSK1]
            assert isinstance(
                the_work_file, Path
            ), f"Unexpected {WRK_MSK1} (not a file?)!"
            os.remove(the_work_file)
