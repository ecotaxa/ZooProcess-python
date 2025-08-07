# Process a scan from its physical acquisition to operator check

from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from ZooProcess_lib.img_tools import get_creation_date
from helpers.paths import file_date
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
        self.modern_fs = ModernScanFileSystem(zoo_project, sample_name, subsample_name)

        # Image inputs
        self.raw_scan, self.bg_scans = get_scan_and_backgrounds(
            self.logger, self.zoo_project, self.subsample_name
        )
        # Outputs
        self.msk_file_path = self.modern_fs.MSK_file_path()

    def prepare(self):
        """
        Start the job execution.
        """
        self.logger = self._setup_job_logger(
            self.modern_fs.ensure_meta_dir() / "mask_gen_job.log"
        )
        # Mark the job as started
        self.mark_started()
        # Log the start of the job execution
        self.logger.info(
            f"Starting post-scan check generation for project: {self.zoo_project.name}, sample: {self.sample_name}, subsample: {self.subsample_name}"
        )
        assert self.raw_scan is not None, "No RAW scan"
        assert len(self.bg_scans) == 2, "No background scan"

    def is_needed(self) -> bool:
        scan_date = get_creation_date(self.raw_scan)
        if self.msk_file_path.exists():
            msk_date = file_date(self.msk_file_path)
            return msk_date <= scan_date
        else:
            return True

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

    def _cleanup_work(self):
        """Clean up the files that the present process is going to (re) create"""
