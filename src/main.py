# import os
import os
import tempfile
from pathlib import Path
from typing import Union, List, OrderedDict

import requests
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import StreamingResponse, Response

from Models import (
    ScanIn,
    Folder,
    BMProcess,
    Background,
    User,
    LoginReq,
    Project,
    Drive,
    Instrument,
    Calibration,
    Sample,
    SubSample,
    Scan,
    SampleWithBackRef,
)
from ZooProcess_lib.Processor import Processor, Lut
from ZooProcess_lib.ZooscanFolder import ZooscanDrive
from auth import get_current_user_from_credentials
from demo_get_vignettes import generate_json
from helpers.web import (
    raise_404,
    get_stream,
    internal_server_error_handler,
    TimingMiddleware,
)
from img_proc.convert import convert_tiff_to_jpeg
from img_proc.process import Process
from legacy.drives import validate_drives
from legacy.files import find_background_file
from legacy_to_remote.importe import import_old_project, getDat1Path, pid2json
from legacy_to_remote.importe import listWorkFolders
from local_DB.db_dependencies import get_db
from logger import logger
from modern.from_legacy import (
    project_from_legacy,
    samples_from_legacy_project,
    backgrounds_from_legacy_project,
    drives_from_legacy,
    scans_from_legacy_project,
    drive_from_legacy,
    sample_from_legacy,
)
from modern.ids import drive_and_project_from_hash
from providers.SeparateServer import SeparateServer
from providers.server import Server
from remote.DB import DB
from remote.TaskStatus import TaskStatus
from separate import Separate
from separate_fn import separate_images
from static.favicon import create_plankton_favicon

# import csv
# import requests
# from separate import separate_multiple

params = {"server": "http://localhost:8081", "dbserver": "http://localhost:8000"}

dbserver = Server("http://zooprocess.imev-mer.fr:8081/v1", "/ping")
server = Server("http://seb:5000", "/")
tunnelserver = Server("http://localhost:5001", "/")
nikoserver = Server("http://niko.obs-vlfr.fr:5000", "/")

# separateServer = SeparateServer(server,dbserver)
separateServer = SeparateServer(tunnelserver, dbserver)

from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from config_rdr import config


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan event handler for application startup and shutdown"""
    # Run validation on application startup
    validate_drives()
    yield
    # Cleanup code (if any) would go here


# Initialize FastAPI with lifespan event handler
app = FastAPI(lifespan=lifespan)

app.add_exception_handler(
    status.HTTP_500_INTERNAL_SERVER_ERROR, internal_server_error_handler
)
# Security scheme for JWT bearer token authentication is imported from auth.py

origins = [
    "*",
    "localhost",
    "zooprocess.imev-mer.fr",
    "localhost:8000",
    "imev:3001",
    # "http://localhost",
    # "http://localhost:8000",
    # "http://localhost:3001",
    # "http://127.0.0.1:59245",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add timing middleware to log execution time of all endpoints
app.add_middleware(TimingMiddleware)


@app.get("/favicon.ico")
def get_favicon():
    """
    Serve a plankton-inspired favicon.

    Returns:
        Response: A response containing the favicon image.
    """
    favicon_bytes = create_plankton_favicon()
    return Response(content=favicon_bytes.getvalue(), media_type="image/x-icon")


@app.get("/")
def read_root():
    # test_db_server = dbserver.test_server() #? "running":"not running";
    # test_server = server.test_server() #? "running":"not running";
    # test_niko = nikoserver.test_server() #? "running":"not running";
    test_tunnel_niko = tunnelserver.test_server()  # ? "running":"not running";

    return {
        "message": "Happy Pipeline",
        "description": "API to separate multiple plankton organisms from Zooprocess images",
        "servers": {
            # "bd": test_db_server ,
            #     "home": test_server,
            # "niko": test_niko,
            "tunnel_niko": test_tunnel_niko
        },
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
def separate(scan: ScanIn) -> None:
    # import os

    logger.info(f"POST /separator/scan: {scan}")

    Separate(scan.scanId, scan.bearer, separateServer)


@app.put("/separate/")
def separate(folder: Folder):
    logger.info(f"PUT /separate/: {folder}")

    srcFolder = folder.path
    # srcFolder = "/Users/sebastiengalvagno/Drives/Zooscan/Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_scan/_work/dyfamed_20230111_200m_d1_1/multiples_to_separate"

    if os.path.isdir(srcFolder):
        logger.info(f"folder: {srcFolder}")
        # return {"folder":folder.path}

        # dest = "/Users/sebastiengalvagno/Drives/Zooscan/Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_scan/_work/dyfamed_20230111_200m_d1_1/multiples_to_separate"

        # id = requests.post("/separator/", json={"folder":folder.path}).json()["id"]
        # id = 1
        # id = None
        # print("id: ", id)
        mask_folder = f"{srcFolder}mask/"
        result_folder = f"{srcFolder}result/"

        # mkdir(mask_folder)
        # mkdir(result_folder)

        db = dbserver
        bearer = None
        taskId = None
        if folder.db != None and folder.bearer != None and folder.taskId != None:
            db = folder.db
            bearer = folder.bearer
            taskId = folder.taskId

        images = separate_images(
            path=srcFolder,
            path_out=mask_folder,
            path_result=result_folder,
            db=db,
            bearer=bearer,
            taskId=taskId,
        )

        # return folder.path
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
    files = {"path1", "path2", "path3"}
    # return {"files":files}
    return files
    # return f"/separate/{folder.path}"
    # return {"files":"files"}


class ImageUrl(BaseModel):
    src: str
    dst: Union[str, None] = None


@app.post("/convert/")
def convert(image: ImageUrl):
    """covert an image from tiff to jpeg format"""

    # dst = image + ".jpg"
    # dst = /Users/sebastiengalvagno/Drives/Zooscan/Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_back/20230229_1219_background_large_manual.tif

    # logger.info(f"converts {image.src} to {image.dst}")

    try:
        file_out = convert_tiff_to_jpeg(image.src, image.dst)
        # logger.info(f"file_out: {file_out}")
        return file_out
        # return {"dst" : file_out }
    except:
        logger.error(f"Cannot convert {image.src}")
        raise HTTPException(status_code=500, detail="Cannot convert the image")


class VignetteFolder(BaseModel):
    src: str
    base: str
    output: str


@app.get("/vignettes/")
def getVignettes(folder: VignetteFolder):
    """get vignettes list from a folder
    return web path to the vignettes list file
    """

    logger.info(f"GET /vignettes/ {folder}")

    try:
        json_data = generate_json(folder.src, folder.base)
        with open(folder.output, "w") as json_file:
            json_file.write(json_data)

        return json_data
    except:
        logger.error("Cannot generate vignettes list")
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


def markTaskWithErrorStatus(taskId, db, bearer, message="error"):
    # import requests
    logger.info("markTaskWithErrorStatus")
    if taskId == None or bearer == None or db == None:
        logger.error("markTaskWithErrorStatus: taskId or bearer or db is None")
        logger.error(f"taskId: {taskId}")
        logger.error(f"bearer: {bearer}")
        logger.error(f"db: {db}")
        return
    url = f"{dbserver.getUrl()}/task/{taskId}"
    logger.info(f"url: {url}")
    body = {"status": "FAILED", "log": message}
    response = requests.post(url, body, headers={"Authorization": f"Bearer {bearer}"})
    logger.info(f"response: {response}")
    logger.info(f"response: {response.status_code}")


def markTaskWithDoneStatus(taskId, db, bearer, message="done"):
    # import requests
    logger.info("markTaskWithDoneStatus")
    if taskId == None or bearer == None or db == None:
        logger.error("markTaskWithDoneStatus: taskId or bearer or db is None")
        logger.error(f"taskId: {taskId}")
        logger.error(f"bearer: {bearer}")
        logger.error(f"db: {db}")

        return

    url = f"{dbserver.getUrl()}/task/{taskId}"
    logger.info(f"url: {url}")
    body = {"status": "FINISHED", "log": message}
    response = requests.post(url, body, headers={"Authorization": f"Bearer {bearer}"})
    logger.info(f"response: {response}")
    logger.info(f"response: {response.status_code}")


def markTaskWithRunningStatus(taskId, db, bearer, message="running"):
    # import requests
    logger.info("markTaskWithRunningStatus")
    if taskId == None or bearer == None or db == None:
        logger.error("markTaskWithRunningStatus: taskId or bearer or db is None")
        logger.error(f"taskId: {taskId}")
        logger.error(f"bearer: {bearer}")
        logger.error(f"db: {db}")

        return

    url = f"{dbserver.getUrl()}/task/{taskId}"
    logger.info(f"url: {url}")
    body = {"status": "RUNNING", "log": message}
    response = requests.post(url, body, headers={"Authorization": f"Bearer {bearer}"})
    logger.info(f"response: {response}")
    logger.info(f"response: {response.status_code}")


def sendImageProcessed(taskId, db, bearer, type, path):
    # import requests
    logger.info("sendImageProcessed")
    if taskId == None or bearer == None or db == None:
        logger.error("sendImageProcessed: taskId or bearer or db is None")
        logger.error(f"taskId: {taskId}")
        logger.error(f"bearer: {bearer}")
        logger.error(f"db: {db}")
        return
    url = f"{dbserver.getUrl()}/scan/{taskId}?nomove&taskid"
    logger.info(f"url: {url}")
    body = {"type": type, "scan": path}
    response = requests.post(url, body, headers={"Authorization": f"Bearer {bearer}"})
    logger.info(f"response: {response}")
    logger.info(f"response: {response.status_code}")


@app.post("/process/")
# def process(folder:Folder):
def process(folder: BMProcess):
    """
    Process a scan

    return hardcoded values for demo because image processing is not implemented yet
    """

    # logger.info(f"scanId OK: {folder.scanId}")

    logger.info("POST /process/")
    logger.info(f"folder: {folder}")
    logger.info(f"src: {folder.src}")
    logger.info(f"dst: {folder.dst}")
    logger.info(f"scan: {folder.scan}")
    logger.info(f"back: {folder.back}")
    logger.info(f"taskId: {folder.taskId}")
    logger.info(f"db: {folder.db}")
    logger.info(f"bearer: {folder.bearer}")

    dst = folder.dst if folder.dst != "" else folder.src

    db = DB(folder.bearer, folder.db)
    taskStatus = TaskStatus(folder.taskId, db)

    # markTaskWithRunningStatus( folder.taskId, folder.db, folder.bearer, "running")
    taskStatus.sendRunning()

    # if ( folder.taskId != None ):
    #     ret = {
    #         "taskId": folder.taskId,
    #         "dst": dst,
    #     }
    # return ret

    # db = folder.db
    # db = dbserver

    if folder.scan == "":
        logger.error("scan is not defined")
        # markTaskWithErrorStatus(folder.taskId, folder.db, folder.bearer, "no scan found")
        taskStatus.sendError("no scan found")
        raise HTTPException(status_code=404, detail="Scan not found")
    if folder.back == "":
        logger.error("back is not defined")
        # markTaskWithErrorStatus(folder.taskId, folder.db, folder.bearer, "no background found")
        taskStatus.sendError("no background found")
        raise HTTPException(status_code=404, detail="Background not found")

    # out = "/uploads/01-10-2024/20230228_1219_back_large_raw_2-1727764546231-800724713.jpg"
    # out = "/Users/sebastiengalvagno/Work/test/nextui/zooprocess_v10/public/uploads/01-10-2024/20230228_1219_back_large_raw_2-1727771577652-46901916001.jpg"

    # out = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_out1.gif"
    # mask = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_msk1.gif"
    # vis = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_vis1.tif"

    process = Process(folder.scan, folder.back, taskStatus, db)

    process.run()

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
    response = requests.get(f"${dbserver.getUrl()}scan/{scanId}")
    if response.ok:
        scan = response.json()
        logger.info(f"scan: {scan}")
        return scan
    else:
        raise HTTPException(status_code=404, detail="Scan not found")


def mediumBackground(back1url, back2url):
    """
    Process the background scans
    """

    logger.info(f"mediumBackground {back1url} {back2url}")
    # @see ZooProcess_lib repo for examples, some config is needed here.
    lut = Lut()
    processor = Processor(None, lut)

    # back : np.ndarray

    path_obj1 = Path(back1url)
    path_obj2 = Path(back2url)

    # Obtenir le chemin sans le filename
    path = str(path_obj1.parent)

    # Obtenir juste le filename
    filename = path_obj1.name
    extraname = "_medium_" + filename
    logger.info(f"mediumBackground path: {path}")
    logger.info(f"mediumBackground filename: {filename}")
    logger.info(f"mediumBackground extraname: {extraname}")
    logger.info(f"mediumBackground back1url: {back1url}")
    logger.info(f"mediumBackground back2url: {back2url}")
    logger.info(f"mediumBackground path_obj: {path_obj1}")
    logger.info(f"mediumBackground path_obj.parent: {path_obj1.parent}")
    logger.info(f"mediumBackground path_obj.name: {path_obj1.name}")
    logger.info(f"mediumBackground path_obj.stem: {path_obj1.stem}")
    logger.info(f"mediumBackground path_obj.suffix: {path_obj1.suffix}")

    _8bits_back1url = Path(path, f"{path_obj1.stem}_8bits{path_obj1.suffix}")
    logger.info(f"_8bits_back1url: {_8bits_back1url}")
    _8bits_back2url = Path(path, f"{path_obj2.stem}_8bits{path_obj2.suffix}")
    logger.info(f"_8bits_back2url: {_8bits_back2url}")
    # _8bits_back1url = Path(path_obj1.parent, path_obj1.stem, "_8bits" , ".tif" )
    # logger.info(f"_8bits_back1url: {_8bits_back1url}")
    # _8bits_back2url = Path(path_obj2.parent, path_obj2.stem, "_8bits" , ".tif" )
    # logger.info(f"_8bits_back2url: {_8bits_back2url}")

    processor.converter.do_file_to_file(Path(back1url), Path(_8bits_back1url))
    processor.converter.do_file_to_file(Path(back2url), Path(_8bits_back2url))

    logger.info("8 bit convert OK")

    # img = loadimage(back1url)
    # backurl = saveimage(img,filename=extraname,path=path)
    # logger.info(f"mediumBackground backurl: {backurl}")

    source_files = [_8bits_back1url, _8bits_back2url]
    backurl = Path(path_obj1.parent, f"{path_obj1.stem}_background_large_manual.tif")
    output_path = backurl

    # logger.info(f"backurl: {backurl.as_uri()}")
    logger.info(f"backurl: {backurl.as_posix()}")

    logger.info("Processing bg_combiner")
    processor.bg_combiner.do_files(source_files, output_path)
    logger.info("Processing bg_combiner done")

    return backurl.as_posix()


@app.post("/background/")
def add_background(background: Background):
    """
    Process the background scans
    """
    logger.info(f"POST /background/ {background}")

    try:
        # back1 = getScanFromDB(background.backgroundId[0])
        # back2 = getScanFromDB(background.backgroundId[1])
        back1 = background.background[0]
        back2 = background.background[1]
    except:
        logger.error("Background scan(s) not found")
        markTaskWithErrorStatus(
            background.taskId,
            background.db,
            background.bearer,
            "Background scan(s) not found",
        )
        raise HTTPException(status_code=404, detail="Backgroud scan(s) not found")

    # if back1.instrumentId == back2.instrumentId:
    #     markTaskWithErrorStatus(background.taskId,background.db,background.bearer,"Background scans must be from the same instrument")
    #     raise HTTPException(status_code=404, detail="Background scans must be from the same instrument")

    markTaskWithRunningStatus(
        background.taskId, background.db, background.bearer, "running"
    )

    back = mediumBackground(back1, back2)

    logger.info(f"back: {back}")

    instrumentId = background.instrumentId
    projectId = background.projectId

    data = {
        # "url": f"http://localhost:8000/background/{back}",
        "url": back,
        # "instrumentId": instrumentId,
        # "projectId": projectId
        "taskId": background.taskId,
        "type": "MEDIUM_BACKGROUND",
    }

    logger.info(f"background(): {data}")

    # save_image(back, "/Users/sebastiengalvagno/Drives/Zooscan/Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_back/20230229_1219_background_large_manual.tif")

    # TODO Mettre dans une fonction car optionnel
    # response = requests.put(url=f"${dbserver.getUrl()}background/{instrumentId}/url?projectId=${projectId}", data=data, headers={"Authorization": f"Bearer {background.bearer}"})
    url = f"{dbserver.getUrl()}/background/{instrumentId}/url?projectId={projectId}"
    logger.info(f"url: {url}")
    response = requests.post(
        url=url, data=data, headers={"Authorization": f"Bearer {background.bearer}"}
    )
    if response.ok:
        markTaskWithDoneStatus(
            background.taskId,
            background.db,
            background.bearer,
            response.json().get("id"),
        )
        logger.info(response.json())
        # return response.json().get("id")
        markTaskWithDoneStatus(
            background.taskId, background.db, background.bearer, "Finished"
        )
        return response.json()
    else:
        logger.error(f"response.status_code: {response.status_code}")
        # if ( response.status_code == 405):
        markTaskWithErrorStatus(
            background.taskId,
            background.db,
            background.bearer,
            "Cannot add medium scan in the DB",
        )
        detail = {
            "status": "partial_success",
            "file_url": back,
            "message": "Data generated successfully, but failed to add to the DB",
            "db_error": response.status_code,
            "taskId": background.taskId,
        }
        # raise HTTPException(status_code=206, detail="Cannot add medium scan in the DB")
        raise HTTPException(status_code=206, detail=detail)
        # else:
        #     markTaskWithErrorStatus(background.taskId, background.db, background.bearer, "Cannot generate medium scan")
        #     raise HTTPException(status_code=response.status_code, detail="Cannot generate medium scan")


# from importe import importe

# importe(app)


def postSample(projectId, sample, bearer, db):
    # url = f"{dbserver.getUrl()}/projects"
    url = f"{db}/projects/{projectId}/samples"
    logger.info(f"url: {url}")

    headers = {"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"}

    response = requests.post(url, json=sample, headers=headers)

    if response.status_code != 200:
        logger.error(f"response: {response}")
        logger.error(f"response text: {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail="Error importing sample: " + response.text,
        )

    logger.info(f"response: {response}")
    logger.info(f"response: {response.status_code}")

    sampleid = response.json().get("id")
    return sampleid


@app.post("/import")
def import_project(project: Project):
    json = import_old_project(project)
    return json


def getProjectDataFromDB(name: str, db: DB):
    logger.info(f"getProjectDataFromDB name: {name}")
    # logger.info(f"getProjectDataFromDB db: {db}")

    # url = db.makeUrl(f'/projects/{name}')
    # logger.info(f"url: {url}")
    # response = db.get(url)

    # response = db.get(f'/projects/{name}')
    # logger.info(f"get projectData: {response}")
    # if response["status"] != "success":
    #     logger.error("Failed to retrieve project data")
    #     return HTTPException(status_code=404, detail="Project not found")

    # logger.info("Project data retrieved successfully")
    # if not response["data"]:
    #     logger.error("Failed to retrieve project data")
    #     return HTTPException(status_code=404, detail="Project not found")

    # projectData = response["data"]
    projectData = db.get(f"/projects/{name}")
    return projectData


@app.post("/login")
def login(login_req: LoginReq, db: Session = Depends(get_db)):
    """
    Login endpoint

    If successful, returns a JWT token which will have to be used in bearer authentication scheme for subsequent calls.
    """
    from auth import create_jwt_token, get_user_from_db

    # Validate the credentials against the database
    user = get_user_from_db(login_req.email, db)

    if (
        not user or user.password != login_req.password
    ):  # In a real app, use proper password hashing
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create user data for the token
    user_data = {
        "sub": user.id,
        "name": user.name,
        "email": user.email,
    }

    # Create a JWT token with 30-day expiration
    token = create_jwt_token(user_data, expires_delta=30 * 24 * 60 * 60)

    # Return the token as a JSON response
    from fastapi.responses import JSONResponse

    return JSONResponse(content=token)


@app.get("/users/me")
def get_current_user(
    user=Depends(get_current_user_from_credentials),
):
    """
    Returns information about the currently authenticated user.

    This endpoint requires authentication using a JWT token obtained from the /login endpoint.
    """
    # Return the user information
    return User(id=user.id, name=user.name, email=user.email)


@app.get("/projects")
@app.get("/projects/{project_hash}")
def get_projects(
    project_hash: str = None,
    user=Depends(get_current_user_from_credentials),
) -> Union[Project, List[Project]]:
    """
    Returns a list of subdirectories inside each element of DRIVES or a specific project if project_id is provided.

    This endpoint requires authentication using a JWT token obtained from the /login endpoint.

    Args:
        project_hash: Optional. If provided, returns the project with the specified ID.
    """
    if project_hash is None:
        return list_all_projects()
    else:
        # If project_hash is provided, return the specific project
        drive_path, project_name, project_path = drive_and_project_from_hash(
            project_hash
        )
        drive_model = Drive(
            id=drive_path.name, name=drive_path.name, url=str(drive_path)
        )
        project = project_from_legacy(drive_model, project_path)
        return project


def list_all_projects(drives_to_check=None):
    """
    List all projects from the specified drives.

    Args:
        drives_to_check: Optional list of drive paths to check. If None, uses config.DRIVES.
        serial_number: Optional serial number to use for projects. Default is "PROD123".

    Returns:
        List of Project objects.
    """
    # Create a list to store all projects
    all_projects = []
    # Use provided drives or default to config.DRIVES
    if drives_to_check is None:
        drives_to_check = config.DRIVES
    # Iterate through each drive in the list
    for drive_path in drives_to_check:
        drive = Path(drive_path)
        drive_model = Drive(id=drive.name, name=drive.name, url=drive_path)
        drive_zoo = ZooscanDrive(drive_path)

        for a_prj_path in drive_zoo.list():
            project = project_from_legacy(drive_model, a_prj_path)
            all_projects.append(project)

    return all_projects


@app.get("/drives")
def get_drives(
    user=Depends(get_current_user_from_credentials),
) -> List[Drive]:
    """
    Returns a list of all drives.
    This endpoint requires authentication using a JWT token obtained from the /login endpoint.
    """
    return drives_from_legacy()


@app.get("/test")
def test(project: Project):
    """
    Temporary API to test the import of a project
    try to link background and subsamples
    try because old project have not information about the links
    links appear only when scan are processed
    then need to parse
    """

    logger.info("test")
    logger.info(f"project: {project}")
    # path = "/Volumes/sgalvagno/plankton/zooscan_zooprocess_test/Zooscan_apero_pp_2023_wp2_sn002/Zooscan_scan/_work"
    # workpath = Path(project.path,"Zooscan_scan/_work")
    # logger.info(f"workpath: {workpath}")

    # folders = listWorkFolders(workpath)
    # # logger.info(f"folders: {folders}")
    # # return folders

    # for folder in folders:
    #     logger.info(f"folder: {folder}")
    #     folder_path = Path(workpath, folder)
    #     logger.info(f"folder_path: {folder_path}")
    #     addVignettesFromSample(folder_path, folder, "Bearer", "db", "projectId")

    # from ProjectClass import ProjectClass

    # projectClass = ProjectClass(project.name,"")

    db = DB(bearer=project.bearer, db=project.db)

    # response = db.get(f'/projects/{project.id}')
    # logger.info(f"get projectData: {response}")
    # if response["status"] != "success":
    #     logger.error("Failed to retrieve project data")
    #     return HTTPException(status_code=404, detail="Project not found")

    # logger.info("Project data retrieved successfully")
    # if not response["data"]:
    #     logger.error("Failed to retrieve project data")
    #     return HTTPException(status_code=404, detail="Project not found")

    # projectData = response["data"]

    if not project.name:
        logger.error("Project name is required")
        project.name = Path(project.path).name
        if not project.name:
            logger.error("Failed to retrieve project data")
            raise HTTPException(status_code=400, detail="Project name is required")

    logger.info(f"project.name: {project.name}")
    projectData = getProjectDataFromDB(project.name, db)
    # logger.info(f"projectData: {projectData}")

    logger.info(f"projecctData.id: {projectData['id']}")
    # response = db.get(f'/projects/{projectData.id}/backgrounds')

    # logger.info(f"response: {response}")
    # if response.status_code == 200:
    #     project.backgrounds = response.json()
    #     logger.info(f"project.backgrounds: {project.backgrounds}")
    # else:
    #     logger.error("Failed to retrieve backgrounds")
    #     raise HTTPException(status_code=400, detail="Backgrounds not found")

    # project.backgrounds = db.get(f'/projects/{projectData["id"]}/backgrounds')
    backgrounds = db.get(f'/projects/{projectData["id"]}/backgrounds')

    # logger.info(f"backgrounds: {backgrounds}")

    workpath = Path(project.path, "Zooscan_scan/_work")
    logger.info(f"workpath: {workpath}")

    samples = projectData["samples"]
    # return samples

    folders = listWorkFolders(workpath)
    # logger.info(f"folders: {folders}")

    for folder in folders:
        logger.info(f"folder: {folder}")
        folder_path = Path(workpath, folder)
        logger.info(f"folder_path: {folder_path}")

        dat_path = getDat1Path(folder_path)
        json_dat = pid2json(dat_path)

        background_correct_using = json_dat["Image_Process"]["Background_correct_using"]
        logger.info(f"background_correct_using: {background_correct_using}")
        image = json_dat["Image_Process"]["Image"]
        logger.info(f"image name: {image}")

        sampleName = json_dat["Sample"]["SampleId"]
        logger.info(f"sampleName: {sampleName}")
        subsampleName = image.replace(".tif", "")
        logger.info(f"subsample: {subsampleName}")

        def searchSample(samples, name):
            for sample in samples:
                if sample["name"] == name:
                    return sample

            return None

        def searchSubSample(subsamples, name):
            for sub in subsamples:
                # if subsampleName in sub[subsampleName]:
                if sub["name"] == name:
                    return sub
            return None

        def searchScan(scans, type):
            for scan in scans:
                if scan["type"] == type:
                    return scan
            return None

        sample = searchSample(samples, sampleName)
        subsample = searchSubSample(sample["subsample"], subsampleName)

        scan = searchScan(sample["scan"], "SCAN")
        if scan is None:
            raise HTTPException(status_code=400, detail="Scan not found")
            # continue

        userId = scan["userId"]

        prefix = background_correct_using.split("_back", 1)[0]
        logger.info(f"prefix: {prefix}")

        for back in backgrounds:
            file = Path(back["url"]).name

            if file.startswith(prefix):
                logger.info(f"file: {file}")
                logger.info(f"back: {back}")

                # remove the back from the backgrounds list
                backgrounds.remove(back)

                # update back with userId
                back["userId"] = userId
                back["subsampleId"] = subsample["id"]

                subsample["scan"].append(back)
                # update the DB
                db.put(f'/backgrounds/{back["id"]}', back)

        # logger.info(f"sample: {sample}")
        # logger.info(f"subsample: {subsample}")

        return subsample
        # return sample
        # return sample["subsample"]
        # # return sample["name"] == folder
        # return {sample, subsample}
        # return 1

    return "test OK"


@app.get("/instruments")
def get_instruments(full: bool = False):
    """
    Returns a list of all instruments.

    Args:
        full (bool, optional): If True, returns the full instrument details. Defaults to False.
    """
    from modern.instrument import get_instruments as get_all_instruments

    instruments = get_all_instruments()

    if not full:
        # Return a simplified version with just id and name
        return [
            {"id": instrument.id, "name": instrument.name} for instrument in instruments
        ]

    return instruments


@app.get("/instruments/{instrument_id}")
def get_instrument(instrument_id: str):
    """
    Returns details about a specific instrument.

    Args:
        instrument_id (str): The ID of the instrument to retrieve.

    Returns:
        Instrument: The instrument with the specified ID.

    Raises:
        HTTPException: If the instrument is not found.
    """
    from modern.instrument import get_instrument_by_id

    instrument = get_instrument_by_id(instrument_id)
    if instrument is None:
        raise HTTPException(
            status_code=404, detail=f"Instrument with ID {instrument_id} not found"
        )
    return instrument


@app.get("/background/{instrument_id}")
def get_backgrounds_by_instrument(instrument_id: str) -> List[Background]:
    """
    Returns the last scanned backgrounds for a given instrument.

    Args:
        instrument_id (str): The ID of the instrument to retrieve backgrounds for.

    Returns:
        List[Background]: A list of backgrounds associated with the instrument.

    Raises:
        HTTPException: If the instrument is not found.
    """
    from modern.instrument import get_instrument_by_id

    # Check if the instrument exists
    instrument = get_instrument_by_id(instrument_id)
    if instrument is None:
        raise HTTPException(
            status_code=404, detail=f"Instrument with ID {instrument_id} not found"
        )

    # Get all projects
    projects = list_all_projects()

    # Collect all backgrounds from all projects
    all_backgrounds = OrderedDict()
    a_project: Project
    for a_project in projects:
        if a_project.instrument.id != instrument_id:
            continue
        zoo_drive = ZooscanDrive(Path(a_project.drive.url))
        project_folder = zoo_drive.get_project_folder(a_project.name)
        # Get backgrounds for this project
        project_backgrounds = backgrounds_from_legacy_project(
            a_project.drive, project_folder
        )
        # Add to the list
        for a_bg in project_backgrounds:
            if a_bg.id not in all_backgrounds:
                all_backgrounds[a_bg.id] = a_bg

    # Sort by creation date (newest first)
    ret = list(all_backgrounds.values())
    ret.sort(key=lambda bg: bg.createdAt, reverse=True)

    return ret


@app.put("/users/{instrumentId}/calibration/{calibrationId}")
def update_calibration(
    instrumentId: str,
    calibrationId: str,
    calibration: Calibration,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
):
    """
    Update a calibration.

    Args:
        instrumentId (str): The ID of the instrument which owns the calibration.
        calibrationId (str): The ID of the calibration to update.
        calibration (Calibration): The updated calibration data.

    Returns:
        Calibration: The updated calibration.

    Raises:
        HTTPException: If the calibration is not found or the user is not authorized.
    """
    from remote.DB import DB
    import modern.calibration as calibration_module

    # Check if the user is authorized to update this calibration
    if user.id != userId:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this calibration"
        )

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Update the calibration
    return calibration_module.update(calibrationId, calibration.dict(), db_instance)


@app.post("/instruments/{instrumentId}/calibration")
def create_calibration(
    instrumentId: str,
    calibration: Calibration,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
):
    """
    Add a calibration to an instrument.

    Args:
        instrumentId (str): The ID of the instrument to add the calibration to.
        calibration (Calibration): The calibration data.

    Returns:
        Calibration: The created calibration.

    Raises:
        HTTPException: If the instrument is not found or the user is not authorized.
    """
    # Check if the instrument exists
    from remote.DB import DB
    from modern.instrument import get_instrument_by_id
    import modern.calibration as calibration_module

    instrument = get_instrument_by_id(instrumentId)
    if instrument is None:
        raise HTTPException(
            status_code=404, detail=f"Instrument with ID {instrumentId} not found"
        )

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Create the calibration
    return calibration_module.create(instrumentId, calibration.dict(), db_instance)


@app.get("/projects/{project_hash}/samples")
def get_samples(
    project_hash: str,
    user=Depends(get_current_user_from_credentials),
) -> List[Sample]:
    """
    Get the list of samples associated with a project.

    Args:
        project_hash (str): The hash of the project to get samples for.

    Returns:
        List[Sample]: A list of samples associated with the project.

    Raises:
        HTTPException: If the project is not found or the user is not authorized.
    """
    logger.info(f"Getting samples for project {project_hash}")

    drive_path, project_name, _ = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    project = zoo_drive.get_project_folder(project_name)

    return samples_from_legacy_project(project)


@app.get("/projects/{project_hash}/backgrounds")
def get_backgrounds(
    project_hash: str, user=Depends(get_current_user_from_credentials)
) -> List[Background]:
    """
    Get the list of backgrounds associated with a project.

    Args:
        project_hash (str): The hash of the project to get backgrounds for.
        user: Security dependency to get the current user.

    Returns:
        List[Background]: A list of backgrounds associated with the project.

    Raises:
        HTTPException: If the project is not found or the user is not authorized.
    """
    logger.info(f"Getting backgrounds for project {project_hash}")

    drive_path, project_name, _ = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    project = zoo_drive.get_project_folder(project_name)

    # Create a Drive model from the drive path
    drive_model = Drive(
        id=Path(drive_path).name, name=Path(drive_path).name, url=drive_path.as_posix()
    )

    return backgrounds_from_legacy_project(drive_model, project)


@app.get("/projects/{project_hash}/scans")
def get_scans(
    project_hash: str,
    # user=Depends(get_current_user_from_credentials)
) -> List[Scan]:
    """
    Get the list of scans associated with a project.

    Args:
        project_hash (str): The hash of the project to get scans for.
        user: Security dependency to get the current user.

    Returns:
        List[ScanIn]: A list of scans associated with the project.

    Raises:
        HTTPException: If the project is not found or the user is not authorized.
    """
    logger.info(f"Getting scans for project {project_hash}")

    drive_path, project_name, _ = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    project = zoo_drive.get_project_folder(project_name)

    return scans_from_legacy_project(project)


@app.get("/projects/{project_hash}/background/{background_id}")
async def get_background(
    project_hash: str,
    background_id: str,
    # user=Depends(get_current_user_from_credentials), # TODO: Should be protected?
) -> StreamingResponse:
    """
    Get a specific background from a project by its ID.

    Args:
        project_hash (str): The hash of the project to get the background from.
        background_id (str): The ID of the background to retrieve from the project.
        user: Security dependency to get the current user.

    Returns:
        Background: The requested background.

    Raises:
        HTTPException: If the project or background is not found
    """
    logger.info(f"Getting background {background_id} for project {project_hash}")

    drive_path, project_name, _ = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    project = zoo_drive.get_project_folder(project_name)

    assert background_id.endswith(
        ".jpg"
    )  # This comes from @see:backgrounds_from_legacy_project
    background_name = background_id[:-4]

    background_file = find_background_file(project, background_name)
    if background_file is None:
        raise_404(
            f"Background with ID {background_id} not found in project {project_hash}"
        )

    tmp_jpg = Path(tempfile.mktemp(suffix=".jpg"))
    convert_tiff_to_jpeg(background_file, tmp_jpg)
    file_like, length, media_type = get_stream(tmp_jpg)
    headers = {"content-length": str(length)}
    return StreamingResponse(file_like, headers=headers, media_type=media_type)


@app.post("/projects/{project_id}/samples")
def create_sample(
    project_hash: str,
    sample: Sample,
    user=Depends(get_current_user_from_credentials),
) -> Sample:
    """
    Add a new sample to a project.

    Args:
        project_hash (str): The ID of the project to add the sample to.
        sample (Sample): The sample data.

    Returns:
        Sample: The created sample.

    Raises:
        HTTPException: If the project is not found or the user is not authorized.
    """
    logger.info(f"Creating sample for project {project_hash}")

    # Check if the project exists
    drive_path, project_name, project_path = drive_and_project_from_hash(project_hash)

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # In a real implementation, you would save the sample to a database
    # For now, we'll just return the sample with a generated ID
    if not sample.id:
        sample.id = f"sample_{len(get_samples(project_hash, user)) + 1}"

    # Try to create the sample in the database
    # This is a placeholder - in a real implementation, you would save the sample to a database
    # For example: created_sample = db_instance.post(f"/projects/{project_hash}/samples", sample.dict())
    # For now, we'll just return the sample
    created_sample = sample

    return created_sample


@app.get("/projects/{project_hash}/samples/{sample_id}")
def get_sample(
    project_hash: str,
    sample_id: str,
    # user=Depends(get_current_user_from_credentials),
) -> SampleWithBackRef:
    """
    Get a specific sample from a project.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to get.

    Returns:
        Sample: The requested sample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Getting sample {sample_id} for project {project_hash}")

    drive_path, project_name, project_path = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    drive_model = drive_from_legacy(drive_path)

    zoo_project = zoo_drive.get_project_folder(project_name)

    # Check if the sample exists in the list of samples
    for sample_name in zoo_project.zooscan_scan.list_samples_with_state():
        if sample_name == sample_id:
            break
    else:
        logger.error(f"Sample with ID {sample_id} not found in project {project_hash}")
        raise HTTPException(
            status_code=404,
            detail=f"Sample with ID {sample_id} not found",
        )

    project = project_from_legacy(drive_model, project_path)
    reduced = sample_from_legacy(sample_name)
    # Return the sample, enriched with back ref
    return SampleWithBackRef(
        **reduced.model_dump(),
        projectId=project.id,
        project=project,
    )


@app.put("/projects/{project_hash}/samples/{sample_id}")
def update_sample(
    project_hash: str,
    sample_id: str,
    sample: Sample,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> Sample:
    """
    Update a specific sample in a project.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to update.
        sample (Sample): The updated sample data.

    Returns:
        Sample: The updated sample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Updating sample {sample_id} for project {project_hash}")

    # Check if the project exists
    try:
        project = get_projects(project_hash, user)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        existing_sample = get_sample(project_hash, sample_id, user)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Ensure the sample ID matches the path parameter
    if sample.id != sample_id:
        raise HTTPException(
            status_code=400,
            detail="Sample ID in the request body does not match the ID in the URL",
        )

    # Try to update the sample in the database
    # This is a placeholder - in a real implementation, you would update the sample in a database
    # For example: updated_sample = db_instance.put(f"/projects/{project_hash}/samples/{sample_id}", sample.dict())
    # For now, we'll just return the sample
    updated_sample = sample

    return updated_sample


@app.delete("/projects/{project_hash}/samples/{sample_id}")
def delete_sample(
    project_hash: str,
    sample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> dict:
    """
    Delete a specific sample from a project.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to delete.

    Returns:
        dict: A message indicating the sample was deleted.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Deleting sample {sample_id} for project {project_hash}")

    # Check if the project exists
    try:
        project = get_projects(project_hash, user, credentials)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        existing_sample = get_sample(project_hash, sample_id, user, credentials)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to delete the sample from the database
    # This is a placeholder - in a real implementation, you would delete the sample from a database
    # For example: db_instance.delete(f"/projects/{project_hash}/samples/{sample_id}")
    # For now, we'll just return a success message
    pass

    return {"message": f"Sample {sample_id} deleted successfully"}


@app.get("/projects/{project_hash}/samples/{sample_id}/subsamples")
def get_subsamples(
    project_hash: str,
    sample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> List[SubSample]:
    """
    Get the list of subsamples associated with a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to get subsamples for.

    Returns:
        List[SubSample]: A list of subsamples associated with the sample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Getting subsamples for sample {sample_id} in project {project_hash}")

    # Check if the project exists
    try:
        project = get_projects(project_hash, user, credentials)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        sample = get_sample(project_hash, sample_id, user, credentials)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to get subsamples from the database
    # This is a placeholder - in a real implementation, you would fetch the subsamples from a database
    # For example: subsamples = db_instance.get(f"/projects/{project_hash}/samples/{sample_id}/subsamples")
    # For now, we'll return a mock list of subsamples
    subsample1 = SubSample(id="subsample1", name="Subsample 1")
    subsample2 = SubSample(id="subsample2", name="Subsample 2")
    subsamples = [subsample1, subsample2]

    return subsamples


@app.post("/projects/{project_hash}/samples/{sample_id}/subsamples")
def create_subsample(
    project_hash: str,
    sample_id: str,
    subsample: SubSample,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> SubSample:
    """
    Add a new subsample to a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to add the subsample to.
        subsample (SubSample): The subsample data.

    Returns:
        SubSample: The created subsample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Creating subsample for sample {sample_id} in project {project_hash}")

    # Check if the project exists
    try:
        project = get_projects(project_hash, user)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        sample = get_sample(project_hash, sample_id, user)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # In a real implementation, you would save the subsample to a database
    # For now, we'll just return the subsample with a generated ID
    if not subsample.id:
        subsample.id = (
            f"subsample_{len(get_subsamples(project_hash, sample_id, user)) + 1}"
        )

    # Try to create the subsample in the database
    # This is a placeholder - in a real implementation, you would save the subsample to a database
    # For example: created_subsample = db_instance.post(f"/projects/{project_hash}/samples/{sample_id}/subsamples", subsample.dict())
    # For now, we'll just return the subsample
    created_subsample = subsample

    return created_subsample


@app.get("/projects/{project_hash}/samples/{sample_id}/subsamples/{subsample_id}")
def get_subsample(
    project_hash: str,
    sample_id: str,
    subsample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> SubSample:
    """
    Get a specific subsample from a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample.
        subsample_id (str): The ID of the subsample to get.

    Returns:
        SubSample: The requested subsample.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    logger.info(
        f"Getting subsample {subsample_id} for sample {sample_id} in project {project_hash}"
    )

    # Check if the project exists
    try:
        project = get_projects(project_hash, user, credentials)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        sample = get_sample(project_hash, sample_id, user, credentials)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to get the subsample from the database
    # This is a placeholder - in a real implementation, you would fetch the subsample from a database
    # For example: subsample = db_instance.get(f"/projects/{project_hash}/samples/{sample_id}/subsamples/{subsample_id}")
    # For now, we'll return a mock subsample
    subsample = SubSample(id=subsample_id, name=f"Subsample {subsample_id}")

    return subsample


@app.delete("/projects/{project_hash}/samples/{sample_id}/subsamples/{subsample_id}")
def delete_subsample(
    project_hash: str,
    sample_id: str,
    subsample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> dict:
    """
    Delete a specific subsample from a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample.
        subsample_id (str): The ID of the subsample to delete.

    Returns:
        dict: A message indicating the subsample was deleted.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    logger.info(
        f"Deleting subsample {subsample_id} for sample {sample_id} in project {project_hash}"
    )

    # Check if the project exists
    try:
        project = get_projects(project_hash, user, credentials)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        sample = get_sample(project_hash, sample_id, user, credentials)
    except HTTPException as e:
        raise e

    # Check if the subsample exists
    try:
        subsample = get_subsample(
            project_hash, sample_id, subsample_id, user, credentials
        )
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to delete the subsample from the database
    # This is a placeholder - in a real implementation, you would delete the subsample from a database
    # For example: db_instance.delete(f"/projects/{project_hash}/samples/{sample_id}/subsamples/{subsample_id}")
    # For now, we'll just return a success message
    pass

    return {"message": f"Subsample {subsample_id} deleted successfully"}


@app.get(
    "/projects/{project_hash}/samples/{sample_id}/subsamples/{subsample_id}/process"
)
def process_subsample(
    project_hash: str,
    sample_id: str,
    subsample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> dict:
    """
    Process a specific subsample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample.
        subsample_id (str): The ID of the subsample to process.

    Returns:
        dict: A message indicating the subsample was processed.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    logger.info(
        f"Processing subsample {subsample_id} for sample {sample_id} in project {project_hash}"
    )

    # Check if the project exists
    try:
        project = get_projects(project_hash, user, credentials)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        sample = get_sample(project_hash, sample_id, user, credentials)
    except HTTPException as e:
        raise e

    # Check if the subsample exists
    try:
        subsample = get_subsample(
            project_hash, sample_id, subsample_id, user, credentials
        )
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to process the subsample
    # This is a placeholder - in a real implementation, you would process the subsample
    # For example: result = db_instance.get(f"/projects/{project_hash}/samples/{sample_id}/subsamples/{subsample_id}/process")
    # For now, we'll just return a success message
    result = {
        "status": "success",
        "message": f"Subsample {subsample_id} processed successfully",
    }

    return result


@app.get("/ping")
def ping():
    """
    Simple health check endpoint that returns 'pong!'.

    This endpoint can be used to verify that the server is running and responding to requests.
    """
    logger.info("Ping endpoint called")
    return "pong!"


@app.get("/crash")
def crash_endpoint():
    """
    Endpoint that deliberately raises an exception to test error handling and logging.

    This endpoint will always return a 500 Internal Server Error and log the stack trace.
    """
    logger.info("Crash endpoint called - about to raise an exception")
    # Deliberately raise an exception
    raise Exception("This is a deliberate crash for testing error handling")


# Start the application when run directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
