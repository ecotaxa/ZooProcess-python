# Process a scan from its physical acquisition to operator check

from pathlib import Path
from typing import List

from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from legacy.ids import (
    mask_file_name,
)
from modern.filesystem import ModernScanFileSystem
from modern.ids import scan_name_from_subsample_name, THE_SCAN_PER_SUBSAMPLE
from modern.jobs.ScanToAutoSep import (
    convert_scan_and_backgrounds,
    get_scan_and_backgrounds,
)
from modern.tasks import Job
from modern.to_legacy import save_mask_image


class FreshScanToCheck(Job):

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
        subsample_dir = self.zoo_project.zooscan_scan.work.get_sub_directory(
            self.subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
        self.modern_fs = ModernScanFileSystem(subsample_dir)
        # Image inputs
        self.raw_scan: Path = Path("xyz")  # Just to keep mypy happy
        self.bg_scans: List[Path] = []

    def prepare(self):
        """
        Start the job execution.
        """
        # Mark the job as started
        self.mark_started()
        # Log the start of the job execution
        self.logger.info(
            f"Starting post-scan check generation for project: {self.zoo_project.name}, sample: {self.sample_name}, subsample: {self.subsample_name}"
        )
        self.raw_scan, self.bg_scans = get_scan_and_backgrounds(
            self.logger, self.zoo_project, self.subsample_name
        )

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
        # Generate MSK with the same name as Legacy, for practicality, but in the modern subdirectory
        meta_dir = self.modern_fs.meta_dir
        msk_file_name = mask_file_name(self.subsample_name)
        msk_file_path = meta_dir / msk_file_name
        # Mask generation
        self.logger.info(f"Generating MSK")
        mask = processor.segmenter.get_mask_from_image(scan_without_background)
        save_mask_image(self.logger, mask, msk_file_path)

    def _cleanup_work(self):
        """Clean up the files that the present process is going to (re) create"""
