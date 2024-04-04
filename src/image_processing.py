import concurrent.futures
import numpy as np


from img_tools import crop, loadimage, saveimage, picheral_median, converthisto16to8, minAndMax, convertImage16to8bit
from ProjectClass import ProjectClass
from SampleClass import SampleClass

from pieceImage import pieceImage
from config import NB_THREADS


def convertPieceOfImage16to8bit(piece:pieceImage) -> np.ndarray:
    return convertImage16to8bit(piece.image, piece.histolut)


def splitimage(image, histolut) -> list:
    shape = image.shape
    print("shape: ", shape)

    cropped = []

    cropped.append(pieceImage(image, 0,                 0,                 image.shape[0]//2-1, image.shape[1]//2-1, histolut))
    cropped.append(pieceImage(image, 0,                 image.shape[0]//2, image.shape[0]//2-1, image.shape[1]//2-1, histolut))
    cropped.append(pieceImage(image, image.shape[1]//2, 0,                 image.shape[0]//2-1, image.shape[1]//2-1, histolut))
    cropped.append(pieceImage(image, image.shape[1]//2, image.shape[0]//2, image.shape[0]//2-1, image.shape[1]//2-1, histolut))

    return cropped


def convertRawScan(pathProject, scan_filename):

    project = ProjectClass(pathProject)

    index = 1
    sample = SampleClass(project, scan_filename, index)

    # rawPath = projet.getPath2RawSample(sample, index)

    # convert(projet, sample, rawPath)
    convert ( sample )

def convert( sample: SampleClass ):

    

    image = loadimage(sample.rawPath())
    median,mean = picheral_median(image)
    min, max = minAndMax(median)
    histolut = converthisto16to8(min,max)
    
    splitted = splitimage(image, histolut)

    print("splitted: ", splitted)

    new_image = np.zeros(image.shape)


    with concurrent.futures.ThreadPoolExecutor(NB_THREADS , "thread_split" ) as executor:
        for split, newimage in zip(splitted, executor.map(convertPieceOfImage16to8bit,splitted)):
            name = f"{split.top}-{split.left}-{split.bottom}-{split.right}"
            print(f"name: {name}")
            new = saveimage(newimage,sample.sample, extraname=name, ext="jpg", path=sample.projet.tempFolder())
            print(f"new picture => {new}")
            new_image[split.left:split.right, split.top:split.bottom] = newimage
        
    new = saveimage(new_image,sample.sample, extraname="treated", ext="jpg", path=sample.projet.tempFolder())
    print(f"result picture => {new}")
