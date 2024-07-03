import os
import PIL
from PIL import Image 
# import cv2
#from numpy import uint16
# import numpy
from PIL.ExifTags import TAGS
# from PIL import ExifTags
# from tools import create_folder

from .img_tools import rename

from pathlib import Path

def create_folder(path: Path):
    
    print("create folder:" , path.as_posix())
    p = Path(path)
    try :
        if not os.path.isdir(path):
            #os.mkdir(path)
            #os.makedirs(path, exist_ok=True)
            p.mkdir(parents=True, exist_ok=True)
    except OSError as error: 
        path_str = str(p.absolute)

        # eprint("cannot create folder: ", path_str ,", ", str(error))
        print("cannot create folder: ", path_str ,", ", str(error))

def print_exif(data):

    for datum in data:
        tag = TAGS.get(datum, datum)
        value = data.get(datum)
        # decode bytes 
        if isinstance(value, bytes):
            value = value.decode()
        print(f"{tag:20}: {value}")

def get_BitsPerSample(data):

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


def get_ExifTag(exifdata, tag):

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

def convert_tiff_to_jpeg(path, path_out, force=None) -> str:
    PIL.Image.MAX_IMAGE_PIXELS = 375000000
    print("EXIF")
    if ( path_out == None):
        print("path_out == None")
        path_out = rename(path, extraname=None, ext="jpg")
        print("path_out: ", path_out)

    if os.path.isfile(path_out) and force != True:
        return path_out

    #TODO : reflechir si on crée le dossier si il n'existe pas ou si on lève une exception
    folder = os.path.dirname(path_out)
    if os.path.isdir(folder) == False:
        print("folder does not exist, creating it", folder)
        # p = Path(folder)
        # path_out = os.path.mkdir(folder)
        # p.mkdir(parents=True, exist_ok=True)
        create_folder(folder)

    print("open image: " , path)
    # image = Image.open(path)
    # Open the TIFF image
    try:
        tiff_image = Image.open(path)

        # print("tiff_image.format_description: ", tiff_image.format_description)
        # print("tiff_image.__dict__:", tiff_image.__dict__)
        # # print("tiff_image.getexif: ", tiff_image.getexif())
        exif_dict = tiff_image.getexif()
        # print_exif(exif_dict)
        # print("tiff_image.getdata: ", tiff_image.getdata())
        # # print("tiff_image.getdata.shape: ", tiff_image.getdata().shape)

        print("converting")

        # image = cv2.imread(path)
        # print("image read")
        # print("image.dtype:", image.dtype)
        # print("image.shape:", image.shape)
        # print("image.size:", image.size)

        # print("image.mode:", image.mode) crash
        # print("image.n_frames:", image.n_frames) crash
        # print("image.info:", image.info) crash
        # print("image.format:", image.format) crash
        # print("image.format_description:", image.format_description) crash
        # print("image.filename:", image.filename) crash
        # if ( image.dtype == uint16):

        # print("get_ifd", tiff_image.getexif().get_ifd(0x8769)) # la date de prise de vue
        # print("get_ifd bit_length", tiff_image.getexif().get_ifd(ExifTags.IFD.bit_length)) crash
        # print("get_ifd bit_count", tiff_image.getexif().get_ifd(ExifTags.IFD.bit_count)) crash
        # print("get_ifd bit_count", tiff_image.getexif().get_ifd(ExifTags.IFD.IFD1.bit_count)) crash



        # BitsPerSample = get_BitsPerSample(exif_dict)
        BitsPerSample = get_ExifTag(exif_dict,"BitsPerSample")
        # XResolution = get_ExifTag(exif_dict,"XResolution")
        # YResolution = get_ExifTag(exif_dict,"YResolution")
        # BitsPerSample = exif_dict['BitsPerSample']
        print("BitsPerSample:", BitsPerSample)
        # print("XResolution:", XResolution)
        # print("YResolution:", YResolution)

        # print ("type(image.dtype): ", type(image.dtype))  retourne toujours uint8 

        # if ( image.dtype == "uint8" ): print("string uint8")

        # if ( image.dtype == "uint16" or BitsPerSample == 16 ): # "uint16"):
        if (BitsPerSample == 16 ): # "uint16"):

            # Convert the image to JPEG format
            # jpeg_image = tiff_image.convert("RGB")
            # jpeg_image = tiff_image.convert("L")

            # image 16bit
            print("uint16")

            # tiff_image.mode = 'I' # a fonctionne mais plus ????
            jpeg_image = tiff_image.point(lambda i:i*(1./256)).convert('L') # .save('my.jpeg')
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

