# Process a scan from its manual separation until sending data to EcoTaxa

from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
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
        subsample_dir = self.zoo_project.zooscan_scan.work.get_sub_directory(
            self.subsample_name, THE_SCAN_PER_SUBSAMPLE
        )
        fs = ModernScanFileSystem(subsample_dir)
        thumbs_dir = fs.cut_dir()
        # TODO, including some force option for dev
        # All separated vignettes should be processed and fresher than corresponding vignette (i.e. ack-ed by someone)

    def run(self):
        # self._cleanup_work()
        processor = Processor.from_legacy_config(
            self.zoo_project.zooscan_config.read(),
            self.zoo_project.zooscan_config.read_lut(),
        )
        # Generate SEP with post-processed vignettes
        # Generate features
        # Generate EcoTaxa data
        # Upload to EcoTaxa

    def _cleanup_work(self):
        """Cleanup the files that present process is going to (re) create"""
