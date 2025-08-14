import os
import tempfile
import time
from pathlib import Path

import pytest
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder

from modern.filesystem import (
    ModernScanFileSystem,
    V10_METADATA_SUBDIR,
    V10_THUMBS_TO_CHECK_SUBDIR,
    ML_SEPARATION_DONE_TXT,
)


def make_fake_zooscan_project(
    base_dir: Path, project_name: str = "TestProject"
) -> ZooscanProjectFolder:
    """Create a minimal Zooscan project folder structure suitable for tests.

    It ensures Zooscan_config/process_install_both_config.txt exists, then returns
    a ZooscanProjectFolder pointing to the created project.
    """
    project_root = Path(base_dir) / project_name
    config_dir = project_root / "Zooscan_config"
    config_dir.mkdir(parents=True, exist_ok=True)
    install_cfg = config_dir / "process_install_both_config.txt"
    if not install_cfg.exists():
        install_cfg.write_text(
            "\n".join(
                [
                    "background_process= last",
                    "minsizeesd_mm= 0.001",
                    "maxsizeesd_mm= 0.001",
                    "upper= 243",
                    "resolution= 1000",
                    "longline_mm= 0.001",
                ]
            )
        )
    return ZooscanProjectFolder(Path(base_dir), project_name)


def test_mark_ML_separation_done():
    """Test that mark_ML_separation_done creates the expected file."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a ModernScanFileSystem instance with a temporary Zooscan project
        project = make_fake_zooscan_project(Path(temp_dir))
        fs = ModernScanFileSystem(
            project, sample_name="Sample1", subsample_name="Sample1_sub1"
        )

        # Call the method to test
        fs.mark_ML_separation_done()

        # Check that the metadata directory was created
        metadata_dir = fs.meta_dir
        assert metadata_dir.exists(), "Metadata directory was not created"
        assert metadata_dir.is_dir(), "Metadata path is not a directory"

        # Check that the separation_done.txt file was created
        separation_done_file = fs.SEP_generated_file_path
        assert separation_done_file.exists(), "txt file was not created"
        assert separation_done_file.is_file(), "txt is not a file"


def test_get_files_modified_before_separation_done():
    """Test that get_files_modified_before_separation_done returns the expected files."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a ModernScanFileSystem instance with a temporary Zooscan project
        project = make_fake_zooscan_project(Path(temp_dir))
        fs = ModernScanFileSystem(
            project, sample_name="Sample1", subsample_name="Sample1_sub1"
        )

        # Create the multiples visualization directory
        multiples_dir = fs.multiples_vis_dir
        os.makedirs(multiples_dir, exist_ok=True)

        # Create some test files in the multiples directory
        # Files that should be included (created before separation_done.txt)
        file1 = multiples_dir / "file1.txt"
        file1.touch()
        file2 = multiples_dir / "file2.txt"
        file2.touch()

        # Wait a moment to ensure different modification times
        time.sleep(0.1)

        # Mark ML separation as done (creates separation_done.txt)
        fs.mark_ML_separation_done()

        # Wait a moment to ensure different modification times
        time.sleep(0.1)

        # Files that should not be included (created after separation_done.txt)
        file3 = multiples_dir / "file3.txt"
        file3.touch()
        file4 = multiples_dir / "file4.txt"
        file4.touch()

        # Call the method to test
        files_before_separation = (
            fs.get_multiples_files_modified_before_separation_done()
        )

        # Check that only the files created before separation_done.txt are returned
        assert len(files_before_separation) == 2, "Expected 2 files to be returned"
        file_names = [f for f in files_before_separation]
        assert "file1.txt" in file_names, "file1.txt should be in the returned files"
        assert "file2.txt" in file_names, "file2.txt should be in the returned files"
        assert (
            "file3.txt" not in file_names
        ), "file3.txt should not be in the returned files"
        assert (
            "file4.txt" not in file_names
        ), "file4.txt should not be in the returned files"
