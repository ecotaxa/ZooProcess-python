from ProjectClass import ProjectClass
from pathlib import Path


class SampleClass:
    
    def __init__(self, project: ProjectClass, sample: str, index: int) -> None:
        self.project = project
        self.sample = sample
        self.index = index

        self.raw = Path(self.project.raw, self.sample + "_raw" + "_" + str(self.index) + ".tif")
        self.work = Path(self.project.work, self.sample + "_" + str(self.index) + ".tif")

    def rawPath(self):
        return self.raw.absolute().as_posix()

    def workPath(self):
        return self.work.absolute().as_posix()

