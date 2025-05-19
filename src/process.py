

#from .SeparateServer import SeparateServer
import requests
from src.DB import DB
from src.img_tools import saveimage


# class Separate:

#     def __init__(self,scanId, bearer, server) -> None:
#         self.scanId = scanId
#         self.bearer = bearer
#         self.dbserver = server.dbserver.getUrl()





#     def getFolder(self):

#         data = {
#             "scanId": self.scanId
#         }

#         headers = {
#             'Authorization': self.bearer,
#         }

#         response = requests.post(
#             url=self.dbserver + "",
#             data=data,
#             headers=headers,
#             timeout=30
#         )


#     def separate(self):
#         pass
        
from src.TaskStatus import TaskStatus
from pathlib import Path
from ZooProcess_lib.Processor import Processor, Lut

class Process:
    """
    A class to process a scan.
    """

    def __init__(self, scan:str, back:str, task:TaskStatus=None, db:DB=None) -> None:
        self.scan = Path(scan)
        self.background = Path(back)
        self.taskStatus = task
        self.db = db
 
        self._8bits_scan = None # path to the 8 bit scan file 
        self.processor = None # the engine

        # file = "/Volumes/sgalvagno/plankton/zooscan_zooprocess_test/Zooscan_apero_pp_2023_wp2_sn002/Zooscan_back/20231010_1509_background_large_manual.tif"
        # self.background = Path(file)
        # fscan = "/Volumes/sgalvagno/plankton/zooscan_zooprocess_test/Zooscan_apero_pp_2023_wp2_sn002/Zooscan_scan/_raw/apero2023_pp_wp2_001_st01_d_d1_raw_1.tif"
        # self.scan = Path(fscan)

    def run(self):

        if self.taskStatus: self.taskStatus.sendRunning("processing")

        lut = Lut()
        lut.resolutionreduct = 2400

        class Config:
            def __init__(self, config_dict):
                for key, value in config_dict.items():
                    setattr(self, key, value)

        config_dict = {"background_process": "last"}
        config = Config(config_dict)
        # self.processor = Processor(None,lut)
        self.processor = Processor(config,lut)


        self.convertScanTo8bits()
        self.removeBackground()
        self.segment()

        self.returnData()

    def convertScanTo8bits(self):
        self._8bits_scan = self.scan.with_suffix(".8bits.tif")
        if self.taskStatus: self.taskStatus.sendRunning("converting scan to 8bit")
        self.processor.converter.do_file_to_file(self.scan, Path(self._8bits_scan))
        # _8bits_scan saved by do_file_to_file
        if self.taskStatus: self.taskStatus.sendRunning("converted scan to 8bit")

    def removeBackground(self):
        if self.taskStatus: self.taskStatus.sendRunning("removing background")

        self.cleaned_scan_image = self.processor.bg_remover.do_from_files(self.background, self._8bits_scan)

        print("bg_remover done")

        # save file
        self.cleaned_scan_file = self._8bits_scan = self.scan.with_suffix(".vis1.tif")
        dest_file = self.cleaned_scan_file.as_posix()
        saveimage(self.cleaned_scan_image, dest_file)

        if self.taskStatus: self.taskStatus.sendRunning("background removed")


    def segment(self):
        if self.taskStatus: self.taskStatus.sendRunning("segmenting")
        pass



    def returnData(self):
        import json

        # fake data
        out = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_out1.gif"
        mask = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_msk1.gif"
        vis = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_vis1.tif"

        ret = {
            "scan": self.scan.as_posix(),
            "back": self.background.as_posix(),
            "mask": mask,
            "out": out,
            "vis": vis,
            "dst": "dst",
        }

        if (self.taskStatus):
            self.taskStatus.sendImage(mask,"MASK")
            self.taskStatus.sendImage(out,"OUT")
            self.taskStatus.sendImage(vis,"VIS")
            self.taskStatus.sendDone(json.dumps(ret))

        return ret
