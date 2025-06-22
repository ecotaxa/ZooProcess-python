# Process a scan from its manual separation until sending data to EcoTaxa

from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from img_proc.generate import generate_separator_gif
from legacy.ids import separator_file_name, mask_file_name
from modern.filesystem import ModernScanFileSystem
from modern.ids import scan_name_from_subsample_name, THE_SCAN_PER_SUBSAMPLE
from modern.tasks import Job


class ManuallySeparatedToEcoTaxa(Job):

    def __init__(
        self, zoo_project: ZooscanProjectFolder, sample_name: str, subsample_name: str
    ):
        super().__init__()
        self.zoo_project = zoo_project
        self.sample_name = sample_name
        self.subsample_name = subsample_name
        self.scan_name = scan_name_from_subsample_name(subsample_name)
        # Modern side
        subsample_dir = self.zoo_project.zooscan_scan.work.get_sub_directory(
            self.subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
        self.modern_fs = ModernScanFileSystem(subsample_dir)

    def prepare(self):
        """
        Start the job execution.
        """
        prj_path = self.zoo_project.path
        # Mark the job as started
        self.mark_started()

        # Log the start of the job execution
        self.logger.info(
            f"Starting post-manual processing for project: {self.zoo_project.name}, sample: {self.sample_name}, subsample: {self.subsample_name}"
        )
        # All vignettes should be generated and fresher than origin data
        thumbs_dir = self.modern_fs.cut_dir()
        # TODO, including some force option for dev
        # All separated vignettes should be processed, i.e. written after marker file

    def run(self):
        # self._cleanup_work()
        processor = Processor.from_legacy_config(
            self.zoo_project.zooscan_config.read(),
            self.zoo_project.zooscan_config.read_lut(),
        )
        # Generate SEP with post-processed vignettes
        # Generate with the same name as Legacy, for practicality, but modern subdirectory
        sep_file_name = separator_file_name(self.subsample_name)
        msk_file_name = mask_file_name(self.subsample_name)
        msk_file_path = self.modern_fs.meta_dir() / msk_file_name
        sep_file_path = self.modern_fs.meta_dir() / sep_file_name
        generate_separator_gif(self.modern_fs.cut_dir(), msk_file_path, sep_file_path)
        # Generate features
        # Generate EcoTaxa data
        # Upload to EcoTaxa

    def _cleanup_work(self):
        """Cleanup the files that present process is going to (re) create"""
