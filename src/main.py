# import os
import os
from pathlib import Path
from typing import List

import requests
from fastapi import FastAPI, HTTPException, Depends
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import Response

from Models import (
    ScanIn,
    Folder,
    BMProcess,
    Background,
    User,
    LoginReq,
    Drive,
    ImageUrl,
    VignetteFolder,
)
from ZooProcess_lib.Processor import Processor, Lut
from auth import get_current_user_from_credentials
from demo_get_vignettes import generate_json
from helpers.web import (
    internal_server_error_handler,
    TimingMiddleware,
    validation_exception_handler,
)
from img_proc.convert import convert_tiff_to_jpeg
from img_proc.process import Process
from legacy.drives import validate_drives
from local_DB.db_dependencies import get_db
from local_DB.models import init_db
from logger import logger
from modern.from_legacy import (
    drives_from_legacy,
)
from providers.SeparateServer import SeparateServer
from providers.server import Server
from remote.TaskStatus import TaskStatus
from routers.instruments import router as instruments_router
from routers.projects import router as projects_router
from routers.samples import router as samples_router
from routers.subsamples import router as subsamples_router
from routers.images import router as images_router
from routers.tasks import router as tasks_router
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
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from auth import create_jwt_token, get_user_from_db, SESSION_COOKIE_NAME
from remote.DB import DB


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan event handler for application startup and shutdown"""
    # Run validation on application startup
    validate_drives()

    # Initialize database tables if they don't exist
    logger.info("Initializing database tables")
    init_db()

    yield
    # Cleanup code (if any) would go here


# Initialize FastAPI with lifespan event handler
app = FastAPI(lifespan=lifespan)

app.add_exception_handler(
    status.HTTP_500_INTERNAL_SERVER_ERROR, internal_server_error_handler
)

# Add exception handler for 422 validation errors
app.add_exception_handler(RequestValidationError, validation_exception_handler)

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

# Include the routers
app.include_router(projects_router)
app.include_router(samples_router)
app.include_router(subsamples_router)
app.include_router(instruments_router)
app.include_router(images_router)
app.include_router(tasks_router)


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


# TODO:
# url: '/link',
# data: '{"scanId":"20210625_0921","subSampleId":"zooscan_lov|Zooscan_triatlas_m158_2019_mtn_200microns_sn001_undefined"}',


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

    # if back1.instrument_id == back2.instrument_id:
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

    return JSONResponse(content=token)


@app.get("/login")
def login_get(email: str, password: str, db: Session = Depends(get_db)):
    """
    GET variant of the login endpoint

    If successful, returns a JWT token which will have to be used in bearer authentication scheme for subsequent calls.

    Note: While this endpoint is provided for convenience, using POST /login is recommended for better security
    as it doesn't expose credentials in URL or server logs.
    """

    # Validate the credentials against the database
    user = get_user_from_db(email, db)

    if (
        not user or user.password != password
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

    # Create a response with the token in the body
    response = JSONResponse(content=token)

    # Set the token in a session cookie
    response.set_cookie(key=SESSION_COOKIE_NAME, value=token, httponly=True)

    return response


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


@app.get("/drives")
def get_drives(
    user=Depends(get_current_user_from_credentials),
) -> List[Drive]:
    """
    Returns a list of all drives.
    This endpoint requires authentication using a JWT token obtained from the /login endpoint.
    """
    return drives_from_legacy()


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
