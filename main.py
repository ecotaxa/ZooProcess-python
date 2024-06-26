from typing import Union

from src.separate_fn import separate_images
# from src.tools import mkdir
from src.img_tools import mkdir

from src.server import Server

# from fastapi import FastAPI
from fastapi import FastAPI, HTTPException

import requests

# from src.separate import separate_multiple

from src.separate import Separate
from src.SeparateServer import SeparateServer

from pydantic import BaseModel

from src.convert import convert_tiff_to_jpeg


params = {
    "server": "http://localhost:8081",
    "dbserver": "http://localhost:8000"
}

dbserver = Server("http://zooprocess.imev-mer.fr:8081", "/v1/ping")
server = Server("http://seb:5000", "/")
nikoserver = Server("http://niko.obs-vlfr.fr:5000", "/")

separateServer = SeparateServer(server,dbserver)


app = FastAPI()

# from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.cors import CORSMiddleware


app = FastAPI()

origins = [
    '*',
    "localhost",
    "zooprocess.imev-mer.fr",
    "localhost:8000",
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

    return {
        "message": "Happy Pipeline",
        "description": "API to separate multiple plankton organisms from Zooprocess images",
        # "servers": {
        #     "bd": test_db_server ,
        #     "home": test_server,
        #     "niko": test_niko
        # }
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


class Folder(BaseModel):
    path: str
    # bearer: str | None = None
    # bd: str | None = None
    bearer: Union[str, None] = None
    db: Union[str, None] = None
    taskId: Union[str, None] = None
    scanId: Union[str, None] = None

class Scan(BaseModel):
    scanId: str
    bearer: str

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

        db = None
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

    print("converts ", image.src, " to ", image.dst)

    try:
        file_out = convert_tiff_to_jpeg(image.src, image.dst)
        return file_out
    except:
        print("Cannot convert ", image.src)
        raise HTTPException(status_code=500, detail="Folder not found") 


