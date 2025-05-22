import os
import PIL
from PIL import Image
from typing import Optional, Any, Dict

from PIL.ExifTags import TAGS

from pathlib import Path

from src.helpers.tools import create_folder

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
    PIL.Image.MAX_IMAGE_PIXELS = 375000000
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
