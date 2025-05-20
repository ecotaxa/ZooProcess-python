
from typing import List, Union

from src.importe import import_old_project, getDat1Path, pid2json

from src.Project import Project
from src.separate_fn import separate_images
# from src.tools import mkdir
from src.img_tools import loadimage, mkdir, saveimage

from src.server import Server

# from fastapi import FastAPI
from fastapi import FastAPI, HTTPException

from pydantic import BaseModel
import requests
import json
# import os
from pathlib import Path
# import csv
from typing import List, Dict, Any
import traceback

from src.Models import Scan, Folder, BMProcess, Background

# import requests

# for /test 
from src.importe import addVignettes, listWorkFolders,addVignettesFromSample

from src.TaskStatus import TaskStatus
from src.DB import DB



# from src.separate import separate_multiple

from src.separate import Separate
from src.SeparateServer import SeparateServer
from src.convert import convert_tiff_to_jpeg
from src.demo_get_vignettes import generate_json

params = {
    "server": "http://localhost:8081",
    "dbserver": "http://localhost:8000"
}

dbserver = Server("http://zooprocess.imev-mer.fr:8081/v1", "/ping")
server = Server("http://seb:5000", "/")
tunnelserver = Server("http://localhost:5001", "/")
nikoserver = Server("http://niko.obs-vlfr.fr:5000", "/")

# separateServer = SeparateServer(server,dbserver)
separateServer = SeparateServer(tunnelserver,dbserver)


# app = FastAPI()

# from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.cors import CORSMiddleware


app = FastAPI()

origins = [
    '*',
    "localhost",
    "zooprocess.imev-mer.fr",
    "localhost:8000",
    "imev:3001",
    # "http://localhost",
    # "http://localhost:8000",
    # "http://localhost:3001",
    # "http://127.0.0.1:59245",
]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
CORSMiddleware,
allow_origins=["*"], # Allows all origins
allow_credentials=True,
allow_methods=["*"], # Allows all methods
allow_headers=["*"], # Allows all headers
)


@app.get("/")
def read_root():

    # test_db_server = dbserver.test_server() #? "running":"not running";
    # test_server = server.test_server() #? "running":"not running";
    # test_niko = nikoserver.test_server() #? "running":"not running";
    test_tunnel_niko = tunnelserver.test_server() #? "running":"not running";

    return {
        "message": "Happy Pipeline",
        "description": "API to separate multiple plankton organisms from Zooprocess images",
        "servers": {
            # "bd": test_db_server ,
        #     "home": test_server,
            # "niko": test_niko,
         "tunnel_niko" : test_tunnel_niko
        }
    }



# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}





# class Item(BaseModel):
#     name: str
#     price: float
#     is_offer: Union[bool, None] = None

# @app.put("/items/{item_id}")
# def update_item(item_id: int, item: Item):
#     return {"item_name": item.name, "item_id": item_id}



@app.post("/separator/scan")
def separate(scan: Scan):
    # import os

    print("POST /separator/scan:", scan)
    
    Separate(scan.scanId, scan.bearer, separateServer)




@app.put("/separate/")
def separate(folder: Folder):
    import os
    
    print("PUT /separate/", folder)

    srcFolder = folder.path
    # srcFolder = "/Users/sebastiengalvagno/Drives/Zooscan/Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_scan/_work/dyfamed_20230111_200m_d1_1/multiples_to_separate"

    if os.path.isdir(srcFolder):
        print("folder: ", srcFolder)
        # return {"folder":folder.path}

        # dest = "/Users/sebastiengalvagno/Drives/Zooscan/Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_scan/_work/dyfamed_20230111_200m_d1_1/multiples_to_separate"

        # id = requests.post("/separator/", json={"folder":folder.path}).json()["id"]
        # id = 1
        # id = None
        # print("id: ", id)
        mask_folder = f"{srcFolder}mask/"
        result_folder = f"{srcFolder}result/"

        mkdir(mask_folder)
        mkdir(result_folder)

        db = dbserver
        bearer = None
        taskId = None
        if ( folder.db!= None and folder.bearer!= None and folder.taskId!= None):
            db = folder.db
            bearer = folder.bearer
            taskId = folder.taskId

        images = separate_images(
            path = srcFolder,
            path_out = mask_folder,
            path_result = result_folder,
            db = db,
            bearer = bearer,
            taskId = taskId
        )

        #return folder.path
        return f"/separate/{id}"

    raise HTTPException(status_code=404, detail="Folder not found") 




@app.get("/separate/{folder}")
# Description : Separate multiple from folder
def getSeparate(folder: str):
    """ 
    Separate multiple from folder
    """
    # got list files from the DB
    # getVignettes( scanId, type = (MASK, MERGE, RAW)

    # id = 1
    files = {
        "path1",
        "path2",
        "path3"
    }
    return files


class ImageUrl(BaseModel):
    src: str
    dst: Union[str, None] = None

@app.post('/convert/')
def convert(image:ImageUrl):
    """ covert an image from tiff to jpeg format """

    try:
        file_out = convert_tiff_to_jpeg(image.src, image.dst)
        # print("file_out: ", file_out)
        return file_out
    except:
        print("Cannot convert ", image.src)
        raise HTTPException(status_code=500, detail="Cannot convert the image") 


class VignetteFolder(BaseModel):
    src: str
    base: str
    output: str

@app.get("/vignettes/")
def getVignettes( folder:VignetteFolder):
    """ get vignettes list from a folder 
        return web path to the vignettes list file
    """

    print("GET /vignettes/ ", folder)

    try:
        json_data = generate_json(folder.src, folder.base)
        with open(folder.output, "w") as json_file:
            json_file.write(json_data)

        return json_data
    except:
        print("Cannot generate vignettes list")
        raise HTTPException(status_code=500, detail="Folder not found")




@app.post("/process/")
def process(folder:BMProcess):
    """
    Process a scan

    return hardcoded values for demo because image processing not implemented yet
    """
    import requests
    import json

    print("POST /process/")
    print("folder: ", folder)
    print("src", folder.src)
    print("dst", folder.dst)
    print("scan", folder.scan)
    print("back", folder.back)
    print("taskId", folder.taskId)
    print("db", folder.db)
    print("bearer", folder.bearer)

    dst = folder.dst if folder.dst != "" else folder.src

    db = DB(folder.bearer,folder.db) if folder.bearer and folder.db else None
    taskStatus = TaskStatus(folder.taskId, db) if folder.taskId and db else None

    if taskStatus: taskStatus.sendRunning("processing")

    if ( folder.scan == "" ) :
        print("scan is not defined")
        if taskStatus: taskStatus.sendError( "no scan found")
        raise HTTPException(status_code=404, detail="Scan not found")
    if ( folder.back == "" ):
        print("back is not defined")
        if taskStatus: taskStatus.sendError( "no background found")
        raise HTTPException(status_code=404, detail="Background not found")


    from src.Process import Process
    
    try:
        process = Process(folder.scan, folder.back, taskStatus, db) 
        process.run()
    except Exception as e:
        print("/process Error:", e)
        if e is HTTPException: raise e
        raise HTTPException(status_code=500, detail=f"Failed: {e}")

    return process.returnData()






def getScanFromDB(scanId):
    """
    Get the scan using the DB information
    """
    import requests

    response = requests.get(f"${dbserver.getUrl()}scan/{scanId}")
    if response.ok:
        scan = response.json()
        print("scan: ", scan)
        return scan
    else:
        raise HTTPException(status_code=404, detail="Scan not found")



@app.post("/background/")
def background(background:Background):
    """
    Process the background scans
    """
    from src.Background import Background

    print("POST /background/", background)
    
    db = DB(background.bearer,background.db) if background.bearer and background.db else None
    taskStatus = TaskStatus(background.taskId, db) if background.taskId and db else None

    try:
        # back1 = getScanFromDB(background.backgroundId[0])
        # back2 = getScanFromDB(background.backgroundId[1])
        back1 = background.background[0]
        back2 = background.background[1]
    except:
        if taskStatus: taskStatus.sendError( "Background scan(s) not found")
        raise HTTPException(status_code=404, detail="Backgroud scan(s) not found")

    backgroundclass = Background([back1,back2], taskStatus, db)
    try:
        medianBackground = backgroundclass.run()
        backgroundclass.sendMediumBackground(background.instrumentId, background.projectId)

    except Exception as e:
        print("/background Exception:", e)
        traceback.print_exc()
        if e is HTTPException: raise e
        raise HTTPException(status_code=500, detail=f"Failed: {e}")

    return backgroundclass.returnData()







def postSample(projectId, sample, bearer, db):
    # url = f"{dbserver.getUrl()}/projects"
    url = f"{db}/projects/{projectId}/samples"
    print("url: ", url)

    
    
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=sample, headers=headers)

    if response.status_code != 200:
        print("response: ", response)
        print("response text: ", response.text)
        raise HTTPException(status_code=response.status_code, detail="Error importing sample: " + response.text)

    print("response: ", response)
    print("response: ", response.status_code)
          
    sampleid = response.json().get("id")
    return sampleid







@app.post("/import")
def import_project(project:Project):

    json = import_old_project(project)
    return json

from src.DB import DB


def getProjectDataFromDB(name:str, db:DB):
        
        print("getProjectDataFromDB name" , name)
        # print("getProjectDataFromDB db" , db)

        # url = db.makeUrl(f'/projects/{name}')
        # print("url:",url)
        # response = db.get(url)

        # response = db.get(f'/projects/{name}')
        # print("get projectData", response)
        # if response["status"] != "success":
        #     print("Failed to retrieve project data")
        #     return HTTPException(status_code=404, detail="Project not found")

        # print("Project data retrieved successfully")
        # if not response["data"]:
        #     print("Failed to retrieve project data")
        #     return HTTPException(status_code=404, detail="Project not found")
        
        # projectData = response["data"]
        projectData = db.get(f'/projects/{name}')
        return projectData

@app.get("/test")
def test(project:Project):
    """
    Temporary API to test the import of a project
    try to link background and subsamples 
    try because old project have not information about the links
    links appear only when scan are processed
    then need to parse 
    """

    print("test")
    print("project",project)
    # path = "/Volumes/sgalvagno/plankton/zooscan_zooprocess_test/Zooscan_apero_pp_2023_wp2_sn002/Zooscan_scan/_work"
    # workpath = Path(project.path,"Zooscan_scan/_work")
    # print("workpath",workpath)

    # folders = listWorkFolders(workpath) 
    # # print("folders",folders)
    # # return folders

    # for folder in folders:
    #     print("folder",folder)
    #     folder_path = Path(workpath, folder)
    #     print("folder_path:",folder_path)
    #     addVignettesFromSample(folder_path, folder, "Bearer", "db", "projectId")

        # from src.ProjectClass import ProjectClass

        # projectClass = ProjectClass(project.name,"")



    try:
        db = DB(bearer=project.bearer, db=project.db)

        # response = db.get(f'/projects/{project.id}')
        # print("get projectData", response)
        # if response["status"] != "success":
        #     print("Failed to retrieve project data")
        #     return HTTPException(status_code=404, detail="Project not found")

        # print("Project data retrieved successfully")
        # if not response["data"]:
        #     print("Failed to retrieve project data")
        #     return HTTPException(status_code=404, detail="Project not found")
        
        # projectData = response["data"]

        if not project.name:
            print("Project name is required")
            project.name = Path(project.path).name
            if not project.name:
                print("Failed to retrieve project data")
                raise HTTPException(status_code=400, detail="Project name is required")

        print("project.name",project.name)
        projectData = getProjectDataFromDB(project.name, db)
        # print("projectData",projectData)


        print("projecctData.id",projectData["id"])
        # response = db.get(f'/projects/{projectData.id}/backgrounds')

        # print("response",response)
        # if response.status_code == 200:
        #     project.backgrounds = response.json()
        #     print("project.backgrounds",project.backgrounds)
        # else:
        #     print("Failed to retrieve backgrounds")
        #     raise HTTPException(status_code=400, detail="Backgrounds not found")

        # project.backgrounds = db.get(f'/projects/{projectData["id"]}/backgrounds')
        backgrounds = db.get(f'/projects/{projectData["id"]}/backgrounds')

        # print("backgrounds",backgrounds)

        workpath = Path(project.path,"Zooscan_scan/_work")
        print("workpath",workpath)

        samples = projectData["samples"]
        # return samples

        folders = listWorkFolders(workpath) 
        # print("folders",folders)

        for folder in folders:
            print("folder",folder)
            folder_path = Path(workpath, folder)
            print("folder_path:",folder_path)

            dat_path = getDat1Path(folder_path)
            json_dat = pid2json(dat_path)

            background_correct_using = json_dat["Image_Process"]["Background_correct_using"]
            print("background_correct_using:", background_correct_using)
            image = json_dat["Image_Process"]["Image"]
            print("image name:", image)

            sampleName = json_dat["Sample"]["SampleId"]
            print("sampleName:", sampleName)
            subsampleName = image.replace(".tif", "")
            print("subsample:", subsampleName)

            def searchSample(samples,name):
                for sample in samples:
                    if sample["name"] == name:
                        return sample

                return None    
            
            def searchSubSample(subsamples,name):
                for sub in subsamples:
                    # if subsampleName in sub[subsampleName]:
                    if sub["name"] == name:
                        return sub
                return None
    
            def searchScan(scans,type):
                for scan in scans:
                    if scan["type"] == type:
                        return scan
                return None
                    
            sample = searchSample(samples,sampleName)
            subsample = searchSubSample(sample["subsample"],subsampleName)

            scan = searchScan(sample["scan"],"SCAN")
            if scan is None:
                raise HTTPException(status_code=400, detail="Scan not found")
                # continue

            userId = scan["userId"]


            prefix = background_correct_using.split('_back', 1)[0]
            print("prefix:", prefix)

            for back in backgrounds:
                file = Path(back["url"]).name
                
                if file.startswith(prefix):
                    print("file:", file)
                    print("back:", back)
                    
                    # remove the back from the backgrounds list
                    backgrounds.remove(back)

                    #update back with userId
                    back["userId"] = userId
                    back["subsampleId"] = subsample["id"]

                    subsample["scan"].append(back)
                    # update the DB
                    db.put(f'/backgrounds/{back["id"]}', back)

            # print("sample",sample)
            # print("subsample",subsample)

            return subsample
            # return sample
            # return sample["subsample"]
            # # return sample["name"] == folder
            # return {sample, subsample}
            # return 1
        


    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed: {e}")
        


    return "test OK"
