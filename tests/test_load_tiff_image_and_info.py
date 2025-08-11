import unittest
from PIL import Image
from PIL.ImageFile import ImageFile
import numpy as np

from typing import Tuple, Optional, Dict, Any, Callable, Union
from pathlib import Path


# from ZooProcess_lib.img_tools import load_tiff_image_and_info


class ImageInfo(Dict[str, Any]):
    @property
    def width(self) -> int:
        return self["Image Size"][0]


def load_tiff_image_and_info(file_path: Path) -> Tuple[ImageInfo, np.ndarray]:
    image = Image.open(file_path)
    info = image_info(image)
    data = np.array(image)
    return info, data

def image_info(image: ImageFile) -> ImageInfo:
    info_dict = {
        "Filename": image.filename,
        "Image Size": image.size,
        "Image Height": image.height,
        "Image Width": image.width,
        "Image Format": image.format,
        "Image Mode": image.mode,
        "Image is Animated": getattr(image, "is_animated", False),
        "Frames in Image": getattr(image, "n_frames", 1),
    }
    
    
file = "/Volumes/sgalvagno/plankton/zooscan_zooprocess_test/Zooscan_apero_pp_2023_wp2_sn002/Zooscan_back/20231010_1509_background_large_manual.tif"
file = "/Volumes/PIQv/local_SebProject/Zooscan_back/2025-05-05_Zooscan_back_medium_2025-05-05_20230913_0950_back_large_1-1746449727557-482770598.tif"

info, bg = load_tiff_image_and_info(file)
# self.assertIsNotNone(info)
# self.assertIsNotNone(bg)

print("bg shape:",bg.shape)
print("info:",info)
