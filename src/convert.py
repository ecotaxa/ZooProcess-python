import os
import PIL
from PIL import Image 
import cv2

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
    try:
        tiff_image = Image.open(path)

        print("tiff_image.format_description: ", tiff_image.format_description)

        print("converting")

        image = cv2.imread(path)
        if ( image.dtype == "uint16"):

            # Convert the image to JPEG format
            # jpeg_image = tiff_image.convert("RGB")
            # jpeg_image = tiff_image.convert("L")

            # image 16bit
            print("uint16")

            # tiff_image.mode = 'I' # a fonctionne mais plus ????
            jpeg_image = tiff_image.point(lambda i:i*(1./256)).convert('L') # .save('my.jpeg')
            # tiff_image.point(lambda i:i*(1./256)).convert('L').save(path_out)

            # if jpeg_image.dtype == "uint16":
            #     print("uint16")
            # tiff_image.mode = 'I'
            # jpeg_image = tiff_image.point(lambda i:i*(1./256))
            #     jpeg_image = jpeg_image.convert('L')
        else:
            print(f"8 bit image {jpeg_image.dtype}")
            jpeg_image = tiff_image.convert("L")

        # Save the JPEG image
        print("saving")
        jpeg_image.save(path_out)
        
        # # image.mode = 'I'
        # # image.point(lambda i:i*(1./256)).convert('L').save(path_out)
        # # imgdst = image.point(lambda i:i*(1./256)).convert('L')
        # # imgdst.save(path_out)

        print("image saved ", path_out)    
        return path_out 


    except:
        print(f"Error: can not open image file: {path}")
        return None
    

    # tiff_image = Image.open(path)

    # # Convert the image to JPEG format
    # print("converting")
    # jpeg_image = tiff_image.convert("RGB")

    # # Save the JPEG image
    # print("saving")
    # jpeg_image.save(path_out)
    
    # # image.mode = 'I'
    # # image.point(lambda i:i*(1./256)).convert('L').save(path_out)
    # # imgdst = image.point(lambda i:i*(1./256)).convert('L')
    # # imgdst.save(path_out)

    # print("image saved ", path_out)    
    # return path_out 

