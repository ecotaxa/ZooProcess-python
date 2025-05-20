
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
    # return {"files":files}
    return files
    # return f"/separate/{folder.path}"
    # return {"files":"files"}


class ImageUrl(BaseModel):
    src: str
    dst: Union[str, None] = None

@app.post('/convert/')
def convert(image:ImageUrl):
    """ covert an image from tiff to jpeg format """

    # dst = image + ".jpg"
    # dst = /Users/sebastiengalvagno/Drives/Zooscan/Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_back/20230229_1219_background_large_manual.tif

    # print("converts ", image.src, " to ", image.dst)

    try:
        file_out = convert_tiff_to_jpeg(image.src, image.dst)
        # print("file_out: ", file_out)
        return file_out
        # return {"dst" : file_out }
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




# @app.post("/process/")
# # def process(folder:Folder):
# def process(folder:BMProcess):
#     """
#     Process a scan
#     """
#     import requests

#     # print("scanId OK: ", folder.scanId)

#     print("POST /process/", folder)

#     # img = {
#     #     "state":"",
#     #     "vignettes": [],
#     #     "mask": "/uploads/01-10-2024/20230228_1219_back_large_raw_2-1727764546231-800724713.jpg",
#     #     "out": "/uploads/01-10-2024/20230228_1219_back_large_raw_2-1727764546231-800724713.jpg",
#     #     "vis": "/uploads/01-10-2024/20230228_1219_back_large_raw_2-1727764546231-800724713.jpg",
#     #     "log": "blabla about job done"
#     # }

#     if ( (folder.scanId == None) or (folder.scanId == "") ):
#         print("scanId is not defined")
#         raise HTTPException(status_code=404, detail="Scan not found")

#     print("scanId OK: ", folder.scanId)

#     url = f"{dbserver.getUrl()}/scan/{folder.scanId}"
#     print("url: ", url)

#     response = requests.get(url, headers={"Authorization": f"Bearer {folder.bearer}"})
#     if response.ok:
#         scan = response.json()
#         # return scan
#         print("scan: ", scan)
#     else:
#         raise HTTPException(status_code=404, detail="Scan not found")

#     response = requests.get(f"${dbserver.getUrl()}/project/{scan.projectId}")
#     if response.ok:
#         project = response.json()
#         print("project: ", project)
#     else:
#         raise HTTPException(status_code=404, detail="Project not found")


#     response = requests.get(f"${dbserver.getUrl()}/project/{scan.projectId}/sample/{scan.sampleId}/subsample/{scan.subsampleId}")
#     if response.ok:
#         sample = response.json()
#         print("sample: ", sample)
#     else:
#         raise HTTPException(status_code=404, detail="Project not found")

#     data = {
#         "background": sample.background,
#     }

#     return (data)


def markTaskWithErrorStatus(taskId,db,bearer,message="error"):
    # import requests
    print("markTaskWithErrorStatus")
    if (taskId == None or bearer == None or db == None): 
        print("markTaskWithErrorStatus: taskId or bearer or db is None")
        print("taskId: ", taskId)
        print("bearer: ", bearer)
        print("db: ", db)
        return
    url = f"{dbserver.getUrl()}/task/{taskId}"
    print("url: ", url)
    body = {
        "status": "FAILED",
        "log": message
    }
    response = requests.post(url, body, headers={"Authorization": f"Bearer {bearer}"})
    print("response: ", response)
    print("response: ", response.status_code)

def markTaskWithDoneStatus(taskId,db,bearer,message="done"):
    # import requests
    print("markTaskWithDoneStatus")
    if (taskId == None or bearer == None or db == None): 
        print("markTaskWithDoneStatus: taskId or bearer or db is None")
        print("taskId: ", taskId)
        print("bearer: ", bearer)
        print("db: ", db)

        return
    
    url = f"{dbserver.getUrl()}/task/{taskId}"
    print("url: ", url)
    body = {
        "status": "FINISHED",
        "log": message
    }
    response = requests.post(url, body, headers={"Authorization": f"Bearer {bearer}"})
    print("response: ", response)
    print("response: ", response.status_code)


def markTaskWithRunningStatus(taskId,db,bearer,message="running"):
    # import requests
    print("markTaskWithRunningStatus")
    if (taskId == None or bearer == None or db == None): 
        print("markTaskWithRunningStatus: taskId or bearer or db is None")
        print("taskId: ", taskId)
        print("bearer: ", bearer)
        print("db: ", db)

        return
    
    url = f"{dbserver.getUrl()}/task/{taskId}"
    print("url: ", url)
    body = {
        "status": "RUNNING",
        "log": message
    }
    response = requests.post(url, body, headers={"Authorization": f"Bearer {bearer}"})
    print("response: ", response)
    print("response: ", response.status_code)



def sendImageProcessed(taskId,db,bearer,type,path):
    # import requests
    print("sendImageProcessed")
    if (taskId == None or bearer == None or db == None):
        print("sendImageProcessed: taskId or bearer or db is None")
        print("taskId: ", taskId)
        print("bearer: ", bearer)
        print("db: ", db)
        return
    url = f"{dbserver.getUrl()}/scan/{taskId}?nomove&taskid"
    print("url: ", url)
    body = {
        "type": type,
        "scan": path
    }
    response = requests.post(url, body, headers={"Authorization": f"Bearer {bearer}"})
    print("response: ", response)
    print("response: ", response.status_code)

@app.post("/process/")
# def process(folder:Folder):
def process(folder:BMProcess):
    """
    Process a scan

    return hardcoded values for demo because image processing not implemented yet
    """
    import requests
    import json

    # print("scanId OK: ", folder.scanId)

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

    #markTaskWithRunningStatus( folder.taskId, folder.db, folder.bearer, "running")
    if taskStatus: taskStatus.sendRunning("processing")

    # if ( folder.taskId != None ): 
    #     ret = {
    #         "taskId": folder.taskId,
    #         "dst": dst,
    #     }
        # return ret

    # db = folder.db
    # db = dbserver

    if ( folder.scan == "" ) :
        print("scan is not defined")
        # markTaskWithErrorStatus(folder.taskId, folder.db, folder.bearer, "no scan found")
        if taskStatus: taskStatus.sendError( "no scan found")
        raise HTTPException(status_code=404, detail="Scan not found")
    if ( folder.back == "" ):
        print("back is not defined")
        # markTaskWithErrorStatus(folder.taskId, folder.db, folder.bearer, "no background found")
        if taskStatus: taskStatus.sendError( "no background found")
        raise HTTPException(status_code=404, detail="Background not found")

    # out = "/uploads/01-10-2024/20230228_1219_back_large_raw_2-1727764546231-800724713.jpg"
    # out = "/Users/sebastiengalvagno/Work/test/nextui/zooprocess_v10/public/uploads/01-10-2024/20230228_1219_back_large_raw_2-1727771577652-46901916001.jpg"

    # out = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_out1.gif"
    # mask = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_msk1.gif"
    # vis = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_vis1.tif"


    from src.Process import Process
    
    try:
        process = Process(folder.scan, folder.back, taskStatus, db) 
        process.run()
    except Exception as e:
        print("/process Error:", e)
        if e is HTTPException: raise e
        raise HTTPException(status_code=500, detail=f"Failed: {e}")

    return process.returnData()


    # ret = {
    #     "scan": folder.scan,
    #     "back": folder.back,
    #     "mask": mask,
    #     "out": out,
    #     "vis": vis,
    #     "dst": dst,
    # }

    # print("ret:",ret)

    # if (folder.taskId != None and folder.bearer != None and folder.db != None):
    #     sendImageProcessed(folder.taskId,folder.db,folder.bearer,"MASK",mask)
    #     sendImageProcessed(folder.taskId,folder.db,folder.bearer,"OUT",out)
    #     sendImageProcessed(folder.taskId,folder.db,folder.bearer,"VIS",vis)
    #     markTaskWithDoneStatus(folder.taskId,folder.db,folder.bearer,json.dumps(ret))

    # return ret




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

# def mediumBackground(back1url, back2url):
#     """
#     Process the background scans
#     """
#     import numpy as np

#     print("mediumBackground", back1url, back2url)
#     from ZooProcess_lib.Processor import Processor, Lut
#     # @see ZooProcess_lib repo for examples, some config is needed here.
#     lut = Lut()
#     processor = Processor(None,lut)


#     # back : np.ndarray

#     from pathlib import Path

#     path_obj1 = Path(back1url)
#     path_obj2 = Path(back2url)

#     # Obtenir le chemin sans le filename
#     path = str(path_obj1.parent)

#     # Obtenir juste le filename
#     filename = path_obj1.name
#     extraname = "_medium_" + filename
#     print("mediumBackground path: ", path)
#     print("mediumBackground filename: ", filename)
#     print("mediumBackground extraname: ", extraname)
#     print("mediumBackground back1url: ", back1url)
#     print("mediumBackground back2url: ", back2url)  
#     print("mediumBackground path_obj: ", path_obj1)
#     print("mediumBackground path_obj.parent: ", path_obj1.parent)
#     print("mediumBackground path_obj.name: ", path_obj1.name)
#     print("mediumBackground path_obj.stem: ", path_obj1.stem)
#     print("mediumBackground path_obj.suffix: ", path_obj1.suffix)


#     _8bits_back1url = Path(path , f"{path_obj1.stem}_8bits{path_obj1.suffix}")
#     print("_8bits_back1url: ", _8bits_back1url)
#     _8bits_back2url = Path(path , f"{path_obj2.stem}_8bits{path_obj2.suffix}")
#     print("_8bits_back2url: ", _8bits_back2url)
#     # _8bits_back1url = Path(path_obj1.parent, path_obj1.stem, "_8bits" , ".tif" )
#     # print("_8bits_back1url: ", _8bits_back1url)
#     # _8bits_back2url = Path(path_obj2.parent, path_obj2.stem, "_8bits" , ".tif" )
#     # print("_8bits_back2url: ", _8bits_back2url)

#     processor.converter.do_file_to_file(Path(back1url), Path(_8bits_back1url))
#     processor.converter.do_file_to_file(Path(back2url), Path(_8bits_back2url))

#     print("8 bit convert OK")

#     # img = loadimage(back1url)
#     # backurl = saveimage(img,filename=extraname,path=path)   
#     # print("mediumBackground backurl: ", backurl)

#     source_files = [ _8bits_back1url , _8bits_back2url ]
#     backurl = Path(path_obj1.parent, f"{path_obj1.stem}_background_large_manual.tif" )
#     output_path = backurl

#     # print("backurl:", backurl.as_uri() )
#     print("backurl:", backurl.as_posix() )

#     print("Processing bg_combiner")
#     processor.bg_combiner.do_files(source_files, output_path)
#     print("Processing bg_combiner done")

#     return  backurl.as_posix()

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
        if e is HTTPException: raise e
        raise HTTPException(status_code=500, detail=f"Failed: {e}")

    return backgroundclass.returnData()

# @app.post("/background/")
# def background_old(background:Background):
#     """
#     Process the background scans
#     """
#     import requests

#     print("POST /background/", background)

#     try:
#         # back1 = getScanFromDB(background.backgroundId[0])
#         # back2 = getScanFromDB(background.backgroundId[1])
#         back1 = background.background[0]
#         back2 = background.background[1]
#     except:
#         markTaskWithErrorStatus( background.taskId, background.db, background.bearer, "Background scan(s) not found")
#         raise HTTPException(status_code=404, detail="Backgroud scan(s) not found")
    
#     # if back1.instrumentId == back2.instrumentId:
#     #     markTaskWithErrorStatus(background.taskId,background.db,background.bearer,"Background scans must be from the same instrument")
#     #     raise HTTPException(status_code=404, detail="Background scans must be from the same instrument")

#     markTaskWithRunningStatus( background.taskId, background.db, background.bearer, "running")

#     back = mediumBackground(back1, back2)

#     print("back :",back)

#     instrumentId = background.instrumentId
#     projectId = background.projectId

#     data = {
#         # "url": f"http://localhost:8000/background/{back}",
#         "url": back,
#         # "instrumentId": instrumentId,
#         # "projectId": projectId
#         "taskId": background.taskId,
#         "type":"MEDIUM_BACKGROUND"
#     }

#     print("background() :",data)

#     # save_image(back, "/Users/sebastiengalvagno/Drives/Zooscan/Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_back/20230229_1219_background_large_manual.tif")

#     #TODO Mettre dans une fonction car optionnel
#     # response = requests.put(url=f"${dbserver.getUrl()}background/{instrumentId}/url?projectId=${projectId}", data=data, headers={"Authorization": f"Bearer {background.bearer}"})
#     url = f"{dbserver.getUrl()}/background/{instrumentId}/url?projectId={projectId}"
#     print("url:",url)
#     response = requests.post(url=url, data=data, headers={"Authorization": f"Bearer {background.bearer}"})
#     if response.ok:
#         markTaskWithDoneStatus( background.taskId, background.db, background.bearer, response.json().get("id"))
#         print(response.json())
#         # return response.json().get("id")
#         markTaskWithDoneStatus( background.taskId, background.db, background.bearer, "Finished")
#         return response.json()
#     else:
#         print("response.status_code:",response.status_code)
#         # if ( response.status_code == 405):
#         markTaskWithErrorStatus( background.taskId, background.db, background.bearer, "Cannot add medium scan in the DB")
#         detail = {
#             "status": "partial_success",
#             "file_url": back,
#             "message": "Data generated successfully, but failed to add to the DB",
#             "db_error": response.status_code,
#             "taskId": background.taskId
#         }
#         # raise HTTPException(status_code=206, detail="Cannot add medium scan in the DB")
#         raise HTTPException(status_code=206, detail=detail)
#         # else:
#         #     markTaskWithErrorStatus(background.taskId, background.db, background.bearer, "Cannot generate medium scan")
#         #     raise HTTPException(status_code=response.status_code, detail="Cannot generate medium scan")


# from importe import importe

# importe(app)





def    postSample(projectId,sample,bearer,db):
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
