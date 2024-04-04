import os
import PIL
from PIL import Image 

from .img_tools import rename

def convert_tiff_to_jpeg(path, path_out, force=None) -> str:
    PIL.Image.MAX_IMAGE_PIXELS = 375000000

    if ( path_out == None):
        print("path_out == None")
        path_out = rename(path, extraname=None, ext="jpg")
        print("path_out: ", path_out)

    if os.path.isfile(path_out) and force != True:
        return path_out

    print("open image: " , path)
    # image = Image.open(path)
    # Open the TIFF image
    tiff_image = Image.open(path)

    # Convert the image to JPEG format
    print("converting")
    jpeg_image = tiff_image.convert("RGB")

    # Save the JPEG image
    print("saving")
    jpeg_image.save(path_out)
    
    # image.mode = 'I'
    # image.point(lambda i:i*(1./256)).convert('L').save(path_out)
    # imgdst = image.point(lambda i:i*(1./256)).convert('L')
    # imgdst.save(path_out)

    print("image saved ", path_out)    
    return path_out 

