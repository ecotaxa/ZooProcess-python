# V10 files when Legacy one are not used
import datetime
import os
import shutil
from pathlib import Path
from typing import Tuple, Optional, List

V10_THUMBS_SUBDIR = "v10_cut"  # Output of full image segmented, 1 byte greyscale PNGs
V10_THUMBS_TO_CHECK_SUBDIR = (
    "v10_multiples"  # Where and how ML determined we should separate, RGB PNGs
)
V10_METADATA_SUBDIR = "v10_meta"  # For unique files

ML_SEPARATION_DONE_TXT = "ML_separation_done.txt"


class ModernScanFileSystem:
    """
    A class to manage the modern file system structure based on a legacy work directory.
    Provides access to various subdirectories used in the modern workflow.
    """

    def __init__(self, legacy_scan_dir: Path):
        """
        Initialize with a legacy work directory.

        Args:
            legacy_scan_dir: Path to the legacy work directory
        """
        self.work_dir = legacy_scan_dir

    def meta_dir(self) -> Path:
        """
        Get the metadata directory path.

        Returns:
            Path to the metadata directory
        """
        return self.work_dir / V10_METADATA_SUBDIR

    def cut_dir(self) -> Path:
        """
        Get the cut/thumbnails directory path.

        Returns:
            Path to the cut/thumbnails directory
        """
        return self.work_dir / V10_THUMBS_SUBDIR

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
        thumbs_dir = self.cut_dir()
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
        multiples_dir = self.multiples_vis_dir()
        if multiples_dir.exists():
            shutil.rmtree(multiples_dir)
        os.makedirs(multiples_dir, exist_ok=True)
        return multiples_dir

    def mark_ML_separation_done(self):
        """
        Mark the ML separation process as done by creating an empty file
        named "separation_done.txt" in the metadata directory.
        """
        metadata_dir = self.meta_dir()
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
        separation_done_file = self.meta_dir() / ML_SEPARATION_DONE_TXT
        assert separation_done_file.exists()

        # Get the modification time of separation_done.txt
        separation_done_time = datetime.datetime.fromtimestamp(
            separation_done_file.stat().st_mtime
        )

        # Get the multiples visualization directory
        multiples_dir = self.multiples_vis_dir()
        assert multiples_dir.exists() and multiples_dir.is_dir()

        # Get all files in the directory that were modified before separation_done.txt
        files_before_separation = []
        for file_path in multiples_dir.iterdir():
            if not file_path.is_file():
                continue

            file_mod_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_mod_time < separation_done_time:
                files_before_separation.append(file_path.name)

        return files_before_separation

    def ensure_meta_dir(self) -> Path:
        meta_dir = self.meta_dir()
        if not meta_dir.exists():
            os.makedirs(meta_dir)
        return meta_dir


def get_directory_date_range(
    directory_path: str,
) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    """
    Determine the date range (earliest and latest modification dates) of all files in a given directory.

    This implementation uses a single pass through the files, updating min/max dates as it goes,
    which is more memory-efficient and faster for large directories than collecting all dates first.

    Args:
        directory_path: Path to the directory to analyze

    Returns:
        A tuple containing (earliest_date, latest_date) as datetime objects.
        If the directory is empty or doesn't exist, returns (None, None).
    """
    path = Path(directory_path)

    if not path.exists() or not path.is_dir():
        return None, None

    earliest_date = None
    latest_date = None

    # Single pass through files, updating min/max as we go
    for f in path.iterdir():
        if not f.is_file():
            continue
        mod_time = datetime.datetime.fromtimestamp(f.stat().st_mtime)
        if earliest_date is None or mod_time < earliest_date:
            earliest_date = mod_time
        if latest_date is None or mod_time > latest_date:
            latest_date = mod_time

    return earliest_date, latest_date
