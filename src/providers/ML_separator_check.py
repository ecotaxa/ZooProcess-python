from pathlib import Path

import cv2

from ZooProcess_lib.Processor import Processor
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from ZooProcess_lib.img_tools import (
    load_image,
    convert_image_to_8bit_flattened,
    saveimage,
)
from helpers.tools import find_directory_with_zooscan_back
from logger import logger
from providers.ML_multiple_separator import LS_PATH, BGR_RED_COLOR


def compare_image_directories(to_separate: Path, separated: Path) -> None:
    """
    Compare images with the same name in two directories, from ZooProcess segmenter point of view.

    Args:
        to_separate: First directory containing images
        separated: Second directory containing images

    """
    logger.info(f"Comparing images in directories: {to_separate} and {separated}")

    # Ensure both directories exist
    if not to_separate.exists() or not to_separate.is_dir():
        raise ValueError(
            f"Directory does not exist or is not a directory: {to_separate}"
        )
    if not separated.exists() or not separated.is_dir():
        raise ValueError(f"Directory does not exist or is not a directory: {separated}")

    # Get all image files in both directories
    image_extensions = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif"]

    to_separate_files = {
        f.name[:-4]: f
        for f in to_separate.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    }

    separated_files = {
        f.name[:-4]: f
        for f in separated.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    }

    # Find common filenames
    common_files = set(to_separate_files.keys()) & set(separated_files.keys())

    logger.info(
        f"Found {len(common_files)} images with the same name in both directories"
    )

    project = find_directory_with_zooscan_back(Path(LS_PATH))
    assert project
    drive = project.parent
    zoo_project = ZooscanProjectFolder(drive, project.name)
    processor = Processor.from_legacy_config(
        zoo_project.zooscan_config.read(),
        zoo_project.zooscan_config.read_lut(),
    )
    # Compare each pair of images
    for filename in common_files:
        not_sep_path = to_separate_files[filename]
        sep_path = separated_files[filename]

        # Load images
        try:
            compare_separated_or_not(processor, filename, not_sep_path, sep_path)
        except Exception as e:
            logger.error(f"Error comparing {filename}: {str(e)}")


def compare_separated_or_not(processor, filename, not_sep_path, sep_path):
    not_sep_img = load_image(not_sep_path, cv2.IMREAD_GRAYSCALE)
    rois_original, _ = processor.segmenter.find_ROIs_in_cropped_image(not_sep_img, 2400)
    sep_img = load_image(sep_path, cv2.IMREAD_COLOR_BGR)
    # Replace all pixels with RED_COLOR with white
    # saveimage(sep_img, "/tmp/t.jpg")
    if len(sep_img.shape) == 3:
        # Create a mask for pixels that match RED_COLOR
        mask_red = (
            (sep_img[:, :, 0] == BGR_RED_COLOR[0])
            & (sep_img[:, :, 1] == BGR_RED_COLOR[1])
            & (sep_img[:, :, 2] == BGR_RED_COLOR[2])
        )

        # Replace matched pixels with white (255, 255, 255)
        sep_img[mask_red] = (255, 255, 255)
        # saveimage(sep_img, "/tmp/t2.jpg")
        # flatten image to 1 byte/pixel
        sep_img = convert_image_to_8bit_flattened(sep_img)
        saveimage(sep_img, f"/tmp/{filename}.jpg")
    rois_separated, _ = processor.segmenter.find_ROIs_in_cropped_image(sep_img, 2400)
    logger.info(
        f"Compared {filename}: ROIs unsep: {len(rois_original)} ROIs separated: {len(rois_separated)}"
    )


def main():
    dir1_path = Path(LS_PATH)
    dir2_path = Path(LS_PATH / "separated")
    compare_image_directories(dir1_path, dir2_path)


if __name__ == "__main__":
    main()
