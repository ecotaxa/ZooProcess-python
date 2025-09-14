# Process a scan from its manual separation until sending data to EcoTaxa

import zipfile

import cv2

from ZooProcess_lib.LegacyMeta import Measurements
from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from ZooProcess_lib.img_tools import load_image, add_separated_mask
from config_rdr import config
from img_proc.generate import generate_separator_gif
from legacy.ids import (
    separator_file_name,
    mask_file_name,
    measure_file_name,
    ecotaxa_tsv_file_name,
)
from modern.filesystem import ModernScanFileSystem
from modern.ids import scan_name_from_subsample_name
from modern.jobs.VignettesToAutoSep import (
    get_scan_and_backgrounds,
    convert_scan_and_backgrounds,
    produce_cuts_and_index,
)
from modern.tasks import Job
from providers.ImageList import ImageList
from providers.ecotaxa_client import EcoTaxaApiClient
from providers.ecotaxa_tsv import EcoTaxaTSV


class VerifiedSeparationToEcoTaxa(Job):

    def __init__(
        self,
        zoo_project: ZooscanProjectFolder,
        sample_name: str,
        subsample_name: str,
        token: str,
        dst_project_id: int,
    ):
        super().__init__(
            (zoo_project, sample_name, subsample_name, token, dst_project_id)
        )
        # Params
        self.zoo_project = zoo_project
        self.sample_name = sample_name
        self.subsample_name = subsample_name
        self.token = token
        self.dst_project_id = int(dst_project_id)
        # Derived
        self.scan_name = scan_name_from_subsample_name(subsample_name)
        # Modern side
        self.modern_fs = ModernScanFileSystem(zoo_project, sample_name, subsample_name)

    def prepare(self):
        """
        Start the job execution.
        """
        self.logger = self._setup_job_logger(
            self.modern_fs.ensure_meta_dir() / "upload_job.log"
        )
        # Log the start of the job execution
        self.logger.info(
            f"Starting post-manual processing for project: {self.zoo_project.name}, sample: {self.sample_name}, subsample: {self.subsample_name}"
        )
        # All vignettes should be generated and fresher than origin data
        thumbs_dir = self.modern_fs.cut_dir
        # TODO, including some force option for dev
        # All separated vignettes should be processed, i.e. written after marker file

    def run(self):
        # self._cleanup_work()
        modern_fs = self.modern_fs
        processor = Processor.from_legacy_config(
            self.zoo_project.zooscan_config.read(),
            self.zoo_project.zooscan_config.read_lut(),
        )
        # Generate SEP with post-processed vignettes
        # Generate with the same name as Legacy, for practicality, but in modern subdirectory
        meta_dir = modern_fs.meta_dir
        sep_file_name = separator_file_name(self.subsample_name)
        sep_file_path = meta_dir / sep_file_name

        msk_file_name = mask_file_name(self.subsample_name)
        msk_file_path = meta_dir / msk_file_name
        measures = Measurements().read(meta_dir / measure_file_name(self.scan_name))
        generate_separator_gif(
            self.logger,
            measures,
            modern_fs.multiples_vis_dir,
            modern_fs.cut_dir,
            msk_file_path,
            sep_file_path,
        )
        # Re-segment from original files and add separators
        raw_scan, bg_scans = get_scan_and_backgrounds(
            self.logger, self.zoo_project, self.subsample_name
        )
        scan_resolution, scan_without_background = convert_scan_and_backgrounds(
            self.logger, processor, raw_scan, bg_scans
        )
        sep_image = load_image(sep_file_path, imread_mode=cv2.IMREAD_GRAYSCALE)
        processed_scan_image = add_separated_mask(scan_without_background, sep_image)
        self.logger.info(f"Segmenting")
        rois, stats = processor.segmenter.find_ROIs_in_image(
            processed_scan_image,
            scan_resolution,
        )
        self.logger.info(f"Segmentation stats: {stats}")
        produce_cuts_and_index(
            self.logger,
            processor,
            modern_fs.fresh_empty_cut_after_dir(),
            None,  # No meta needed
            processed_scan_image,
            scan_resolution,
            rois,
            self.scan_name,
        )
        before_cuts = modern_fs.images_in_cut_after_dir()
        after_cuts = modern_fs.images_in_cut_dir()
        self.log_image_diffs(before_cuts, after_cuts)
        # Generate features
        self.logger.info(f"Generating features")
        features = processor.calculator.ecotaxa_measures_list_from_roi_list(
            processed_scan_image, scan_resolution, rois
        )
        # Generate EcoTaxa data
        tsv_file_name = ecotaxa_tsv_file_name(self.subsample_name)
        tsv_file_path = meta_dir / tsv_file_name
        self.logger.info(f"Writing ecotaxa TSV into {tsv_file_path}")
        tsv_gen = EcoTaxaTSV(
            self.zoo_project,
            self.sample_name,
            self.subsample_name,
            self.scan_name,
            rois,
            features,
            self.created_at,
            scan_resolution,
            processor.segmenter,
            bg_scans,
        )
        tsv_gen.generate_into(tsv_file_path)
        # Build images zip
        images_zip = ImageList(modern_fs.cut_dir_after)
        zip_file = images_zip.zipped(self.logger, force_RGB=False)
        # Add the TSV file to the zip
        with zipfile.ZipFile(zip_file, "a") as zip_ref:
            zip_ref.write(tsv_file_path, arcname=tsv_file_name)

        # Upload to EcoTaxa
        assert self.token is not None, "No connection to EcoTaxa"

        client = EcoTaxaApiClient.from_token(
            self.logger, config.ECOTAXA_SERVER, self.token
        )
        self.logger.info(f"Connected as {client.whoami().name}")
        # Upload the zip file into a directory, it automatically uncompresses there
        dest_user_dir = f"/{self.subsample_name}/"
        remote_ref = client.put_file(zip_file, dest_user_dir)
        self.logger.info(f"Zip file uploaded into {dest_user_dir} as {remote_ref}")
        # Start an import task with the file
        job_id = client.import_my_file_into_project(self.dst_project_id, dest_user_dir)
        self.logger.info(f"Waiting for job {job_id}")
        final_job_state = client.wait_for_job_done(job_id)
        if final_job_state.state != "F":
            assert final_job_state.errors is not None
            assert False, "Job failed:" + "\n".join(final_job_state.errors)

    def log_image_diffs(self, before_cuts, after_cuts):
        """
        Log the differences between two sets of images.

        Args:
            before_cuts: List of image filenames before processing
            after_cuts: List of image filenames after processing
        """
        # Convert lists to sets for efficient comparison
        before_set = set(before_cuts)
        after_set = set(after_cuts)

        # Find common images (present in both before and after)
        common_images = before_set.intersection(after_set)

        # Find appearing images (present in after but not in before)
        appearing_images = after_set - before_set
        appearing_msg = ",".join(appearing_images)[:256]

        # Find disappearing images (present in before but not in after)
        gone_images = before_set - after_set
        gone_msg = ",".join(gone_images)[:256]

        # Log the results
        self.logger.info(f"Image differences summary:")
        self.logger.info(f"  - Common images: {len(common_images)} images")
        self.logger.info(f"  - Appearing images: {appearing_msg}")
        self.logger.info(f"  - Disappearing images: {gone_msg} ")

        # Log detailed lists if there are differences
        # if appearing_images:
        #     self.logger.info(f"New images appearing after processing:")
        #     for img in sorted(appearing_images):
        #         self.logger.info(f"  + {img}")
        #
        # if gone_images:
        #     self.logger.info(f"Images that disappeared after processing:")
        #     for img in sorted(gone_images):
        #         self.logger.info(f"  - {img}")

    def _cleanup_work(self):
        """Cleanup the files that the present process is going to (re) create"""
