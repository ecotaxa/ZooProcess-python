
from img_tools import crop, loadimage, saveimage, picheral_median, converthisto16to8, minAndMax, convertImage16to8bit


class pieceImage:

    # def __init__(self, image, pos, top, left, width, height):
    def __init__(self, image, top, left, width, height, histolut):
        # self.image = image
        # self.pos = pos # an id to known the part position
        self.histolut = histolut
        self.top = top
        self.left = left
        self.bottom = top + height
        self.right = left + width
        print(f"pieceImage {self.top}:{self.left} - {self.bottom}:{self.right}")
        self.image = self.crop(image)

    def crop(self,image):
        print(f"crop {self.top}:{self.left} - {self.bottom}:{self.right}")
        return crop(image, self.top, self.left, self.bottom, self.right )
    
    def get_image(self):
        return self.image
    
