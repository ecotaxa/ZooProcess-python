# V10 files when Legacy one are not used
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from legacy.ids import mask_file_name
from modern.ids import THE_SCAN_PER_SUBSAMPLE

V10_THUMBS_SUBDIR = "v10_cut"  # Output of full image segmented, 1 byte greyscale PNGs
V10_THUMBS_TO_CHECK_SUBDIR = (
    "v10_multiples"  # Where and how ML determined we should separate, RGB PNGs
)
V10_METADATA_SUBDIR = "v10_meta"  # For unique files
V10_THUMBS_AFTER_SUBDIR = (
    "v10_cut_after"  # Output of full image segmented, after separation
)

ML_SEPARATION_DONE_TXT = "ML_separation_done.txt"
ML_MSK_OK_TXT = "MSK_validated.txt"


class ModernScanFileSystem:
    """
    A class to manage the modern file system structure based on a legacy work directory.
    Provides access to various subdirectories used in the modern workflow.
    """

    def __init__(
        self, zoo_project: ZooscanProjectFolder, sample_name: str, subsample_name: str
    ):
        """
        Initialize with a legacy work directory.
        """
        self.subsample_name = subsample_name
        self.work_dir = zoo_project.zooscan_scan.work.get_sub_directory(
            subsample_name, THE_SCAN_PER_SUBSAMPLE
        )

    @property
    def meta_dir(self) -> Path:
        """
        Get the metadata directory path.

        Returns:
            Path to the metadata directory
        """
        return self.work_dir / V10_METADATA_SUBDIR

    @property
    def cut_dir(self) -> Path:
        """
        Get the cut/thumbnails directory path.

        Returns:
            Path to the cut/thumbnails directory
        """
        return self.work_dir / V10_THUMBS_SUBDIR

    @property
    def cut_dir_after(self) -> Path:
        """
        Get the cut/thumbnails directory path.

        Returns:
            Path to the cut/thumbnails directory
        """
        return self.work_dir / V10_THUMBS_AFTER_SUBDIR

    @property
    def multiples_vis_dir(self) -> Path:
        """
        Get the multiples visualization directory path.

        Returns:
            Path to the multiples visualization directory
        """
        return self.work_dir / V10_THUMBS_TO_CHECK_SUBDIR

    def fresh_empty_cut_dir(self) -> Path:
        """
        Get the cut/thumbnails directory path, ensuring it's new and empty.
        If the directory exists, it will be removed and recreated.

        Returns:
            Path to a new and empty cut/thumbnails directory
        """
        thumbs_dir = self.cut_dir
        if thumbs_dir.exists():
            shutil.rmtree(thumbs_dir)
        os.makedirs(thumbs_dir, exist_ok=True)
        return thumbs_dir

    def fresh_empty_cut_after_dir(self) -> Path:
        """
        Get the cut/thumbnails directory path, ensuring it's new and empty.
        If the directory exists, it will be removed and recreated.

        Returns:
            Path to a new and empty cut/thumbnails directory
        """
        thumbs_dir = self.cut_dir_after
        if thumbs_dir.exists():
            shutil.rmtree(thumbs_dir)
        os.makedirs(thumbs_dir, exist_ok=True)
        return thumbs_dir

    def fresh_empty_multiples_vis_dir(self) -> Path:
        """
        Get the multiples visualization directory path, ensuring it's new and empty.
        If the directory exists, it will be removed and recreated.

        Returns:
            Path to a new and empty multiples visualization directory
        """
        multiples_dir = self.multiples_vis_dir
        if multiples_dir.exists():
            shutil.rmtree(multiples_dir)
        os.makedirs(multiples_dir, exist_ok=True)
        return multiples_dir

    def mark_ML_separation_done(self):
        """
        Mark the ML separation process as done by creating an empty file
        named "separation_done.txt" in the metadata directory.
        """
        metadata_dir = self.meta_dir
        os.makedirs(metadata_dir, exist_ok=True)
        separation_done_file = metadata_dir / ML_SEPARATION_DONE_TXT
        separation_done_file.touch()

    def get_multiples_files_modified_before_separation_done(self) -> List[str]:
        """
        Get all files in the multiples visualization directory that were last modified
        before the separation_done.txt file was created.

        Returns:
            List[Path]: A list of Path objects representing files modified before separation_done.txt
        """
        # Get the separation_done.txt file path
        separation_done_file = self.meta_dir / ML_SEPARATION_DONE_TXT
        assert separation_done_file.exists()

        # Get the modification time of separation_done.txt
        separation_done_time = datetime.fromtimestamp(
            separation_done_file.stat().st_mtime
        )

        # Get the multiples visualization directory
        multiples_dir = self.multiples_vis_dir
        assert multiples_dir.exists() and multiples_dir.is_dir()

        # Get all files in the directory that were modified before separation_done.txt
        files_before_separation = []
        for file_path in multiples_dir.iterdir():
            if not file_path.is_file():
                continue

            file_mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_mod_time < separation_done_time:
                files_before_separation.append(file_path.name)

        return files_before_separation

    def ensure_meta_dir(self) -> Path:
        meta_dir = self.meta_dir
        if not meta_dir.exists():
            os.makedirs(meta_dir, exist_ok=True)
        return meta_dir

    def images_in_cut_dir(self):
        return [a_file.name for a_file in self.cut_dir.iterdir()]

    def images_in_cut_after_dir(self):
        return [a_file.name for a_file in self.cut_dir_after.iterdir()]

    def mark_MSK_validated(self, event_date: datetime):
        """
        Mark the MSK as validated by writing the date into a file
        """
        metadata_dir = self.ensure_meta_dir()
        validation_file = metadata_dir / ML_MSK_OK_TXT
        with open(validation_file, "w") as f:
            f.write(event_date.strftime("%Y-%m-%d %H:%M:%S"))

    def MSK_file_path(self):
        return self.meta_dir / mask_file_name(self.subsample_name)
