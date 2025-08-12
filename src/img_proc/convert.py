import os
import tempfile
from pathlib import Path
from typing import Optional, Any, Dict

import PIL
import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS

from ZooProcess_lib.img_tools import (
    load_zipped_image,
    saveimage,
    load_tiff_image_and_info,
    loadimage,
)

PIL.Image.MAX_IMAGE_PIXELS = 520_000_000

from helpers.tools import create_folder
from helpers.logger import logger


# def create_folder(path: Path):

#     print("create folder:" , path.as_posix())
#     p = Path(path)
#     try :
#         if not os.path.isdir(path):
#             #os.mkdir(path)
#             #os.makedirs(path, exist_ok=True)
#             p.mkdir(parents=True, exist_ok=True)
#             print("folder created: ", path.absolute())
#     except OSError as error:
#         path_str = str(p.absolute())


#         # eprint("cannot create folder: ", path_str ,", ", str(error))
#         print("cannot create folder: ", path_str ,", ", str(error))
def print_exif(data: Dict[Any, Any]) -> None:
    for datum in data:
        tag = TAGS.get(datum, datum)
        value = data.get(datum)
        # decode bytes
        if isinstance(value, bytes):
            value = value.decode()
        print(f"{tag:20}: {value}")


def get_BitsPerSample(data: Dict[Any, Any]) -> Optional[Any]:
    for datum in data:
        tag = TAGS.get(datum, datum)
        value = data.get(datum)
        # decode bytes
        if isinstance(value, bytes):
            value = value.decode()
        # print(f"{tag:20}: {value}")
        if tag == "BitsPerSample":
            return value

    return None


def get_ExifTag(exifdata: Dict[Any, Any], tag: str) -> Optional[Any]:
    for datum in exifdata:
        embendedtag = TAGS.get(datum, datum)
        value = exifdata.get(datum)
        # decode bytes
        if isinstance(value, bytes):
            value = value.decode()
        # print(f"{tag:20}: {value}")
        if embendedtag == tag:
            return value

    return None


def convert_tiff_to_jpeg(
    path: Path,
    path_out: Optional[Path] = None,
    force: Optional[bool] = None,
) -> Optional[Path]:
    # print("EXIF")
    if path_out is None:
        # print("path_out == None")
        path_out = path.with_suffix("jpg")
    # print("path_out: ", path_out)

    if path_out.is_file() and force is not True:
        # print("file already exists: ", path_out)
        return path_out

    # TODO : reflechir si on crée le dossier si il n'existe pas ou si on lève une exception
    folder = os.path.dirname(path_out)
    # print("folder: ", folder)
    if os.path.isdir(folder) == False:
        # print("folder does not exist, creating it", folder)
        create_folder(Path(folder))

    # print("open image: " , path)
    # image = Image.open(path)
    # Open the TIFF image
    try:
        tiff_image = Image.open(path)

        exif_dict = tiff_image.getexif()

        # print("converting")
        BitsPerSample = get_ExifTag(exif_dict, "BitsPerSample")
        # print("BitsPerSample:", BitsPerSample)

        if BitsPerSample == 16:  # "uint16"):

            # Convert the image to JPEG format
            # jpeg_image = tiff_image.convert("RGB")
            # jpeg_image = tiff_image.convert("L")

            # image 16bit
            print("uint16")

            # tiff_image.mode = 'I' # a fonctionne mais plus ????
            jpeg_image = tiff_image.point(lambda i: i * (1.0 / 256)).convert(
                "L"
            )  # .save('my.jpeg')
            # jpeg_image.save('my.jpeg')
            # tiff_image.point(lambda i:i*(1./256)).convert('L').save(path_out)

            # if jpeg_image.dtype == "uint16":
            #     print("uint16")
            # tiff_image.mode = 'I'
            # jpeg_image = tiff_image.point(lambda i:i*(1./256))
            #     jpeg_image = jpeg_image.convert('L')
        else:
            print(f"8 bit image")
            # jpeg_image = tiff_image.convert("L")
            jpeg_image = tiff_image
            # print(f"jpeg_image {jpeg_image.dtype}")

        # Save the JPEG image
        print("saving")
        jpeg_image.save(path_out)

        print("image saved >", path_out, "<")
        return path_out

    except:
        print(f"Error: can not open image file: {path}")
        raise Exception("Can not open image file: {path}")
        return None


def not_found_image() -> np.ndarray:
    """
    Returns an 8-bit white image with text in the middle.
    The image is in OpenCV convention (numpy ndarray).
    """
    # Create a white image (255 for all pixels)
    width, height = 800, 600
    img = np.ones((height, width), dtype=np.uint8) * 255

    # Add text in the middle
    text = "Image Not Found"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    font_thickness = 2
    text_color = 0  # Black color (0 for grayscale image)

    # Get text size to center it
    text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2

    # Put text on the image
    cv2.putText(
        img, text, (text_x, text_y), font, font_scale, (text_color,), font_thickness
    )

    return img


def resize_if_too_big(img: np.ndarray) -> np.ndarray:
    """
    Check if the input image is larger than 1800 pixels in any dimension.
    If so, resize it while maintaining the aspect ratio.

    Args:
        img: Input image as numpy array

    Returns:
        Resized image if needed, otherwise the original image
    """
    # Get image dimensions
    height, width = img.shape[:2]

    # Check if image is too big
    max_dimension = 1800
    if width <= max_dimension and height <= max_dimension:
        return img  # Image is not too big, return as is

    # Calculate new dimensions while maintaining aspect ratio
    if width > height:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    else:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))

    # Resize the image
    resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

    return resized_img


def convert_image_for_display(img_path: Path) -> Path:
    img_name = img_path.name
    tmp_jpg = Path(tempfile.mktemp(suffix=".jpg"))
    if img_name.endswith(".tif"):
        # Convert the TIF file to JPG
        img_info, img = load_tiff_image_and_info(img_path)
        logger.info(f"Image info (tif): {img_info}")
    elif img_name.endswith(".zip"):
        img_info, img = load_zipped_image(img_path)
        logger.info(f"Image info (zip): {img_info}")
    elif img_name.endswith(".gif"):
        # GIFs are too big for Firefox, they display OK (but slooow) in Chromium
        img = loadimage(img_path)
    else:
        logger.info(f"Can't convert {img_path} with unknown extension")
        img = not_found_image()
    img_smaller = resize_if_too_big(img)
    if "_out1.gif" in img_path.name:
        img_smaller = 255 - img_smaller  # Invert OUT which is white on black
    saveimage(img_smaller, tmp_jpg)
    return tmp_jpg
