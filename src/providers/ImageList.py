import io
import os
import tempfile
import zipfile
from logging import Logger
from pathlib import Path
from typing import List, Optional, Dict
from zipfile import ZipInfo

from PIL import Image


class ImageList:
    """
    A class that lists PNG images from a given directory and stores them internally.

    Attributes:
        directory_path (Path): Path to the directory containing images.
        images (List[Path]): List of paths to PNG or JPG images in the directory
    """

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
        self.size_by_name: Dict[str, int] = {}

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
        Split the images into sublists of specified size and yields ImageList instances.
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

    def zipped(
        self, logger: Logger, force_RGB=True, zip_path: Optional[Path] = None
    ) -> Path:
        """
        Zips flat all images from this ImageList to a temporary zip file.
        Images are converted to RGB if it's not their format.
        A fresh, unique temporary zip file is created for each call (thread-safe).

        Args:
            logger: for messages
            force_RGB: ensure gray-level images are converted to RGB before zipping
            zip_path: destination zip, default to temporary space if not provided

        Returns:
            Path to the temporary zip file
        """
        logger.debug(f"Zipping images from directory: {self.directory_path}")

        # Always create a unique temporary zip file per call (thread-safe)
        if zip_path is None:
            temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
            zip_path = Path(temp_zip.name)
            temp_zip.close()
        logger.debug(f"Created zip file at {zip_path}")

        try:
            image_names = self.get_images()

            # Create the zip file (valid even if there are no images)
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                if not image_names:
                    logger.warning(
                        "No images found in the ImageList; creating empty zip"
                    )
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
                    self.size_by_name[image_name] = pil_img.size[0] * pil_img.size[1]

            logger.debug(
                f"Successfully created zip file with {len(image_names)} images from ImageList at {zip_path}"
            )
            return zip_path

        except Exception as e:
            logger.error(f"Error creating zip file: {str(e)}")
            # If an error occurs, return the path anyway so the caller can handle it
            return zip_path
