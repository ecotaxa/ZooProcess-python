# type:ignore
from src.DB import DB
from src.img_tools import saveimage
from src.TaskStatus import TaskStatus
from pathlib import Path
from typing import List, Tuple
import numpy as np

from ZooProcess_lib.Processor import Processor, Lut
import requests
from fastapi import HTTPException


class Background:

    def __init__(
        self, back: List[str], task: TaskStatus | None = None, db: DB | None = None
    ) -> None:

        self.back = back  # list of paths to background images
        self.taskStatus = task
        self.db = db

        self._8bits_background = None  # path to the 8 bit background file
        self.processor = None  # the engine

    def run(self):

        if self.taskStatus:
            self.taskStatus.sendRunning("running")

        lut = Lut()
        lut.resolutionreduct = 2400
        processor = Processor(None, lut)

        self.definePath()

        processor.converter.do_file_to_file(
            Path(self.back[0]), Path(self._8bits_back1url)
        )
        processor.converter.do_file_to_file(
            Path(self.back[1]), Path(self._8bits_back2url)
        )

        if self.taskStatus:
            self.taskStatus.sendRunning("8 bit converted")

        print("median background outputPath:", self.outputPath.as_posix())

        print("Processing bg_combiner")
        source_files = [self._8bits_back1url, self._8bits_back2url]
        processor.bg_combiner.do_files(source_files, self.outputPath)
        print("Processing bg_combiner done")
        if self.taskStatus:
            self.taskStatus.sendRunning("Background combiner done")

    def definePath(self):
        path_obj1 = Path(self.back[0])
        path_obj2 = Path(self.back[1])

        path = str(path_obj1.parent)

        filename = path_obj1.name
        extraname = "_medium_" + filename

        print("mediumBackground path: ", path)
        print("mediumBackground filename: ", filename)
        print("mediumBackground extraname: ", extraname)
        print("mediumBackground back1url: ", self.back[0])
        print("mediumBackground back2url: ", self.back[1])
        print("mediumBackground path_obj: ", path_obj1)
        print("mediumBackground path_obj.parent: ", path_obj1.parent)
        print("mediumBackground path_obj.name: ", path_obj1.name)
        print("mediumBackground path_obj.stem: ", path_obj1.stem)
        print("mediumBackground path_obj.suffix: ", path_obj1.suffix)

        self._8bits_back1url = Path(path, f"{path_obj1.stem}_8bits{path_obj1.suffix}")
        print("_8bits_back1url: ", self._8bits_back1url)
        self._8bits_back2url = Path(path, f"{path_obj2.stem}_8bits{path_obj2.suffix}")
        print("_8bits_back2url: ", self._8bits_back2url)

        self.outputPath = Path(
            path_obj1.parent, f"{path_obj1.stem}_background_large_manual.tif"
        )
        # output_path = backurl

        return self.outputPath

    def sendMediumBackground(self, instrumentId: str, projectId: str):

        if self.taskStatus and self.db:
            # self.taskStatus.sendImage(self.outputPath, "MEDIUM_BACKGROUND")

            data = {
                "url": self.outputPath,
                "taskId": self.taskStatus.id,
                "type": "MEDIUM_BACKGROUND",
            }

            # url__ = f"{self.db. dbserver.getUrl()}/background/{instrumentId}/url?projectId={projectId}"

            url = self.db.makeUrl(
                f"/background/{instrumentId}/url?projectId={projectId}"
            )
            print("url:", url)
            response = requests.post(url=url, data=data, headers=self.db.getHeader())
            if response.ok:
                id = response.json().get("id")
                self.taskStatus.sendDone(f"Medium Background: {id}")
                # markTaskWithDoneStatus( background.taskId, background.db, background.bearer, response.json().get("id"))
                # print(response.json())
                # return response.json().get("id")
                self.taskStatus.sendDone(f"Finished")
                # markTaskWithDoneStatus( background.taskId, background.db, background.bearer, "Finished")
                # return response.json()
            else:
                print("response.status_code:", response.status_code)
                # if ( response.status_code == 405):
                self.taskStatus.sendError(f"Cannot add medium scan in the DB")
                # markTaskWithErrorStatus( background.taskId, background.db, background.bearer, "Cannot add medium scan in the DB")

                detail = {
                    "status": "partial_success",
                    "file_url": self.outputPath,
                    "message": "Data generated successfully, but failed to add to the DB",
                    "db_error": response.status_code,
                    "taskId": self.taskStatus.id,
                }
                # raise HTTPException(status_code=206, detail="Cannot add medium scan in the DB")
                raise HTTPException(status_code=206, detail=detail)

    def returnData(self):

        data = {
            # "url": f"http://localhost:8000/background/{back}",
            "url": self.back,
            # "instrumentId": instrumentId,
            # "projectId": projectId
            # "taskId": self.taskStatus.taskId,
            "type": "MEDIUM_BACKGROUND",
        }

        if self.taskStatus:
            data["taskId"] = self.taskStatus.id

        return {}
