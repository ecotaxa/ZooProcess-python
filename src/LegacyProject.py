

import ProjectClass
from pathlib import Path
import Project

from importe import getInstrumentFromSN

class LegacyProject(ProjectClass):
    """
    Properties:
        project_name: the name of the project
        home: the folder containing the project
        folder: the project path
    """

    def __init__(self, project_name, piqvFolder , outputFolder = None) -> None:
        super().__init__(project_name, piqvFolder , outputFolder)

    # def __init__(self,path:str):
    #     self.project_name=Path(path).name
    #     self.piqvhome=self.project_name.parent
    #     self.home = Path(self.piqvhome)
    #     self.folder = Path(path)

    #     if Path(self.folder).exists() == False:
    #         # raise HTTPException(status_code=404, detail=f"Project path '{self.folder}' does not exist")
    #         raise "Project path '{self.folder}' does not exist"

    def __init__(self, project: Project):
        # self.project_name = Path(project.path).name
        self.project_name = project.name if project.name != None else Path(project.path).name
        self.piqvhome=self.project_name.parent
        self.home = Path(self.piqvhome)
        self.folder = Path(project.path)

        if Path(self.folder).exists() == False:
            # raise HTTPException(status_code=404, detail=f"Project path '{self.folder}' does not exist")
            raise "Project path '{self.folder}' does not exist"

        self.instrumentSN = project.instrumentSerialNumber
        if self.instrumentSN != None:
            self.instrument = getInstrumentFromSN(project.db, project.bearer, self.instrumentSN)
            print("instrument: ", self.instrument)
    # else:
        if self.instrument == None:
            # need to read a PID file to determine the instrument
            # pidfile = searchPidFile(project.path)

            # piddata = pid2json(pidfile)
            # PID the project does not contain inforation about the instrument
            # then user need to give the instrument serial number or create it before import
            # raise HTTPException(status_code=404, detail="Instrument serial number not found. You need to create the instrument before import")
            raise "Instrument serial number not found. You need to create the instrument before import"
        


    def importProject(self):
    
        pass