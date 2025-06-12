# Process a scan from its background until segmentation
import os
import time
from pathlib import Path
from typing import List

from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder, WRK_MSK1
from ZooProcess_lib.img_tools import get_creation_date
from modern.ids import THE_SCAN_PER_SUBSAMPLE
from modern.tasks import Job
from modern.to_legacy import save_mask_image


class BackgroundAndScanToSegmented(Job):

    def __init__(
        self, zoo_project: ZooscanProjectFolder, sample_name: str, subsample_name: str
    ):
        super().__init__()
        self.zoo_project = zoo_project
        self.sample_name = sample_name
        self.subsample_name = subsample_name
        # Image inputs
        self.raw_scan: Path = Path("/tmp")
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

        # TEMPORARY, TODO: Ensure a consistent 8-bit scan is present
        zooscan_scan = self.zoo_project.zooscan_scan
        self.eight_bit_scan = zooscan_scan.get_file_produced_from(raw_scan.name)
        for_msg = self.eight_bit_scan.relative_to(prj_path)
        assert (
            self.eight_bit_scan.exists()
        ), f"Need {for_msg} to proceed to segmentation"
        eight_bit_date = get_creation_date(self.eight_bit_scan)
        assert (
            eight_bit_date > raw_scan_date
        ), f"Combined scan {for_msg} date is _before_ raw background date"

    def run(self):
        self._cleanup_work()
        time.sleep(10)  # TODO: Remove
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
        # Sample pre-processing
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
        self.logger.info(f"stats: {stats}")

    def _cleanup_work(self):
        work_files = self.zoo_project.zooscan_scan.work.get_files(
            self.subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
        if WRK_MSK1 in work_files:
            os.remove(work_files[WRK_MSK1])
