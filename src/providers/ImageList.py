import os
import tempfile
import zipfile
import io
from logging import Logger
from pathlib import Path
from typing import List, Optional
from zipfile import ZipInfo

from PIL import Image


class ImageList:
    """
    A class that lists PNG images from a given directory and stores them internally.

    Attributes:
        directory_path (Path): Path to the directory containing images
        images (List[Path]): List of paths to PNG images in the directory
        _temp_zip_path (Path): Path to the temporary zip file (class variable)
    """

    _temp_zip_path: Optional[Path] = None

    @classmethod
    def cleanup_temp_zip(cls):
        """
        Clean up the temporary zip file if it exists.
        This method should be called when the program exits or when the temporary file is no longer needed.
        """
        if cls._temp_zip_path is not None and cls._temp_zip_path.exists():
            try:
                cls._temp_zip_path.unlink()
                cls._temp_zip_path = None
            except Exception:
                # Ignore errors when cleaning up
                pass

    def __init__(self, directory_path: Path, images: Optional[List[str]] = None):
        """
        Initialize the ImageList with a directory path and list all PNG images.

        Args:
            directory_path (Path): Path to the directory containing images
            images (List[Path], optional): List of image paths to use instead of loading from directory
        """
        self.directory_path = directory_path
        self.images: List[str] = []
        if images is not None:
            self.images = images
        else:
            self._load_images()

    def _load_images(self) -> None:
        """
        Load all PNG images from the directory and store them internally.
        Images are sorted by name to ensure consistent ordering.
        """
        if not self.directory_path.exists() or not self.directory_path.is_dir():
            return

        self.images = sorted(
            [
                x
                for x in os.listdir(self.directory_path)
                if x.endswith(".png") or x.endswith(".jpg")
            ]
        )

    def get_images(self) -> List[str]:
        """
        Get the list of PNG image names.

        Returns:
            List[str]: List of paths to PNG images
        """
        return self.images

    def count(self) -> int:
        """
        Get the number of PNG images.

        Returns:
            int: Number of PNG images
        """
        return len(self.images)

    def is_empty(self) -> bool:
        """
        Check if there are no PNG images.

        Returns:
            bool: True if there are no PNG images, False otherwise
        """
        return len(self.images) == 0

    def refresh(self) -> None:
        """
        Refresh the list of PNG images from the directory.
        """
        self._load_images()

    def split(self, size: int):
        """
        EcoTaxa that splits the images into sublists of specified size and yields ImageList instances.

        Args:
            size (int): Size of each sublist

        Yields:
            ImageList: ImageList instance containing a subset of the original images
        """
        if size <= 0:
            raise ValueError("Size must be a positive integer")

        # Split the images into sublists of the specified size
        for i in range(0, len(self.images), size):
            sublist = self.images[i : i + size]
            # Create a new ImageList instance with the same directory_path but with only the images from the sublist
            yield ImageList(self.directory_path, images=sublist)

    def zipped(self, logger: Logger, force_RGB=True) -> Path:
        """
        Zips flat all images from this ImageList to a temporary zip file.
        Images are converted to RGB if it's not their format.
        Reuses the same temporary zip file if it already exists.

        Args:
            logger: for messages

        Returns:
            Path to the temporary zip file
        """
        logger.debug(f"Zipping images from directory: {self.directory_path}")

        # Create a temporary file with .zip extension if it doesn't exist yet
        if ImageList._temp_zip_path is None or not ImageList._temp_zip_path.exists():
            temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
            ImageList._temp_zip_path = Path(temp_zip.name)
            temp_zip.close()
            logger.debug(
                f"Created new temporary zip file at {ImageList._temp_zip_path}"
            )
        else:
            logger.debug(
                f"Reusing existing temporary zip file at {ImageList._temp_zip_path}"
            )

        try:
            image_names = self.get_images()

            if not image_names:
                logger.warning("No images found in the ImageList")
                return ImageList._temp_zip_path

            # Create a zip file (overwriting if it already exists)
            with zipfile.ZipFile(ImageList._temp_zip_path, "w") as zip_file:
                # Add each image to the zip file
                for image_name in image_names:
                    image_path = self.directory_path / image_name
                    pil_img = Image.open(image_path)
                    if force_RGB and pil_img.mode != "RGB":
                        cvt_pil_img = pil_img.convert("RGB")
                        img_buffer = io.BytesIO()
                        cvt_pil_img.save(img_buffer, format="PNG")
                        img_buffer.seek(0)
                        # Add the image from the buffer to the zip file
                        zip_file.writestr(ZipInfo(image_name), img_buffer.getvalue())
                    else:
                        zip_file.write(image_path, arcname=image_name)

            logger.debug(
                f"Successfully created zip file with {len(image_names)} images from ImageList at {ImageList._temp_zip_path}"
            )
            return ImageList._temp_zip_path

        except Exception as e:
            logger.error(f"Error creating zip file: {str(e)}")
            # If an error occurs, return the path anyway so the caller can handle it
            return ImageList._temp_zip_path
