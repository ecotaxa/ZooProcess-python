# Process a scan from its physical acquisition to operator check
from pathlib import Path
from typing import List

from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from modern.filesystem import ModernScanFileSystem
from modern.ids import scan_name_from_subsample_name
from modern.jobs.VignettesToAutoSep import (
    convert_scan_and_backgrounds,
    get_scan_and_backgrounds,
    produce_cuts_and_index,
)
from modern.tasks import Job
from modern.to_legacy import save_mask_image
from providers.ML_multiple_classifier import classify_all_images_from


class FreshScanToVignettes(Job):

    def __init__(
        self,
        zoo_project: ZooscanProjectFolder,
        sample_name: str,
        subsample_name: str,
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
        # Image inputs
        self.raw_scan: Path = Path("")
        self.bg_scans: List[Path] = []
        # Outputs
        self.msk_file_path = self.modern_fs.MSK_file_path
        self.scores_file: Path = self.modern_fs.scores_file_path

    def prepare(self):
        """
        Start the job execution.
        Pre-requisites:
            - 2 RAW backgrounds
            - 1 RAW scan
        Process a scan from its background until the first segmentation and automatic separation.
        """
        self.logger = self._setup_job_logger(
            self.modern_fs.ensure_meta_dir() / "mask_gen_job.log"
        )
        # Log the start of the job execution
        self.logger.info(
            f"Starting post-scan check generation for project: {self.zoo_project.name}, sample: {self.sample_name}, subsample: {self.subsample_name}"
        )
        # Collect inputs
        self.raw_scan, self.bg_scans = get_scan_and_backgrounds(
            self.logger, self.zoo_project, self.subsample_name
        )
        assert self.raw_scan is not None, "No RAW scan"
        assert len(self.bg_scans) == 2, "No background scan"

    def run(self):
        # self._cleanup_work()
        processor = Processor.from_legacy_config(
            self.zoo_project.zooscan_config.read(),
            self.zoo_project.zooscan_config.read_lut(),
        )
        self.logger.info(f"Converting scan and backgrounds")
        scan_resolution, scan_without_background = convert_scan_and_backgrounds(
            self.logger, processor, self.raw_scan, self.bg_scans
        )
        # Mask generation
        self.logger.info(f"Generating MSK")
        mask = processor.segmenter.get_mask_from_image(scan_without_background)
        save_mask_image(self.logger, mask, self.msk_file_path)
        # Segmentation
        self.logger.info(f"Segmenting")
        rois, stats = processor.segmenter.find_ROIs_in_image(
            scan_without_background,
            scan_resolution,
        )
        self.logger.info(f"Segmentation stats: {stats}")
        modern_fs = ModernScanFileSystem(
            self.zoo_project, self.sample_name, self.subsample_name
        )
        # "Vignettes"
        self.logger.info(f"Producing thumbnails")
        cut_dir = modern_fs.fresh_empty_cut_dir()
        produce_cuts_and_index(
            self.logger,
            processor,
            cut_dir,
            modern_fs.meta_dir,
            scan_without_background,
            scan_resolution,
            rois,
            self.scan_name,
        )
        # Multiples classification
        self.logger.info(f"Classifying thumbnails")
        maybe_multiples, error = classify_all_images_from(
            self.logger, cut_dir, self.scores_file, 0.4
        )
        assert error is None, error

    def _cleanup_work(self):
        """Clean up the files that the present process is going to (re) create"""
