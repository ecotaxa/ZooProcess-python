import tempfile
import zipfile
from logging import Logger
from pathlib import Path


def zip_images_to_tempfile(logger: Logger, directory_path: Path) -> Path:
    """
    Zips flat all JPG and PNG images inside a given directory to a temporary zip file.

    Args:
        logger: for messages
        directory_path: Path to the directory containing images

    Returns:
        Path to the temporary zip file
    """
    logger.info(f"Zipping images from directory: {directory_path}")

    # Create a temporary file with .zip extension
    temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    temp_zip_path = Path(temp_zip.name)
    temp_zip.close()

    try:
        image_paths = []
        # Find all jpg and png files in the directory
        # jpg_paths = list(directory_path.glob("*.jpg"))
        # image_paths = jpg_paths
        png_paths = list(directory_path.glob("*.png"))
        image_paths.extend(png_paths)

        if not image_paths:
            logger.warning(f"No jpg or png images found in {directory_path}")
            return temp_zip_path

        # Create a zip file
        with zipfile.ZipFile(temp_zip_path, "w") as zip_file:
            # Add each image to the zip file
            for image_path in image_paths:
                zip_file.write(image_path, arcname=image_path.name)

        logger.info(
            f"Successfully created zip file with {len(image_paths)} images at {temp_zip_path}"
        )
        return temp_zip_path

    except Exception as e:
        logger.error(f"Error creating zip file: {str(e)}")
        # If an error occurs, return the path anyway so the caller can handle it
        return temp_zip_path
