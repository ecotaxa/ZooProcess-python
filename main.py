from typing import List, Union

from src.separate_fn import separate_images
# from src.tools import mkdir
from src.img_tools import loadimage, mkdir, saveimage

from src.server import Server

# from fastapi import FastAPI
from fastapi import FastAPI, HTTPException

from pydantic import BaseModel
import requests
import json
import os
from pathlib import Path
import csv
from typing import List, Dict, Any


# import requests

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


app = FastAPI()

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


class Folder(BaseModel):
    path: str
    # bearer: str | None = None
    # bd: str | None = None
    bearer: Union[str, None] = None
    db: Union[str, None] = None
    taskId: Union[str, None] = None
    scanId: Union[str, None] = None

class Background(BaseModel):
    # path: str
    # bearer: str | None = None
    # bd: str | None = None
    bearer: Union[str, None] = None
    db: Union[str, None] = None
    taskId: Union[str, None] = None
    # back1scanId: str
    # back2scanId: str
    projectId: str
    background: List[str]
    instrumentId: str

class BMProcess(BaseModel):
    src: str
    dst: Union[str, None] = None
    scan: str
    back: str
    taskId: Union[str, None] = None
    bearer: Union[str, None] = None
    db: Union[str, None] = None

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

    print("converts ", image.src, " to ", image.dst)

    try:
        file_out = convert_tiff_to_jpeg(image.src, image.dst)
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

    # if ( folder.taskId != None ): 
    #     ret = {
    #         "taskId": folder.taskId,
    #         "dst": dst,
    #     }
        # return ret

    db = folder.db
    # db = dbserver

    if ( folder.scan == "" ) :
        print("scan is not defined")
        markTaskWithErrorStatus(folder.taskId,db,folder.bearer,"no scan found")
        raise HTTPException(status_code=404, detail="Scan not found")
    if ( folder.back == "" ):
        print("back is not defined")
        markTaskWithErrorStatus(folder.taskId,db,folder.bearer,"no background found")
        raise HTTPException(status_code=404, detail="Background not found")

    # out = "/uploads/01-10-2024/20230228_1219_back_large_raw_2-1727764546231-800724713.jpg"
    # out = "/Users/sebastiengalvagno/Work/test/nextui/zooprocess_v10/public/uploads/01-10-2024/20230228_1219_back_large_raw_2-1727771577652-46901916001.jpg"

    out = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_out1.gif"
    mask = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_msk1.gif"
    vis = "/Users/sebastiengalvagno/piqv/plankton/zooscan_lov/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/t_17_2_tot_1_vis1.tif"

    ret = {
        "scan": folder.scan,
        "back": folder.back,
        "mask": mask,
        "out": out,
        "vis": vis,
        "dst": dst,
    }

    print("ret:",ret)

    if (folder.taskId != None and folder.bearer != None and db != None):
        sendImageProcessed(folder.taskId,db,folder.bearer,"MASK",mask)
        sendImageProcessed(folder.taskId,db,folder.bearer,"OUT",out)
        sendImageProcessed(folder.taskId,db,folder.bearer,"VIS",vis)
        markTaskWithDoneStatus(folder.taskId,db,folder.bearer,json.dumps(ret))

    return ret


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

def mediumBackground(back1url, back2url):
    """
    Process the background scans
    """
    import numpy as np

    print("POST /background/", back1url, back2url)

    # back : np.ndarray

    from pathlib import Path

    path_obj = Path(back1url)

    # Obtenir le chemin sans le filename
    path = str(path_obj.parent)

    # Obtenir juste le filename
    filename = path_obj.name
    extraname = "medium_" + filename
    print("mediumBackground path: ", path)
    print("mediumBackground filename: ", filename)
    print("mediumBackground extraname: ", extraname)
    print("mediumBackground back1url: ", back1url)
    print("mediumBackground back2url: ", back2url)  
    print("mediumBackground path_obj: ", path_obj)
    print("mediumBackground path_obj.parent: ", path_obj.parent)
    print("mediumBackground path_obj.name: ", path_obj.name)
    print("mediumBackground path_obj.stem: ", path_obj.stem)
    print("mediumBackground path_obj.suffix: ", path_obj.suffix)

    img = loadimage(back1url)
    backurl = saveimage(img,filename=extraname,path=path)   
    print("mediumBackground backurl: ", backurl)

    return  backurl



@app.post("/background/")
def background(background:Background):
    """
    Process the background scans
    """
    import requests

    print("POST /background/", background)

    try:
        # back1 = getScanFromDB(background.backgroundId[0])
        # back2 = getScanFromDB(background.backgroundId[1])
        back1 = background.background[0]
        back2 = background.background[1]
    except:
        markTaskWithErrorStatus( background.taskId, background.db, background.bearer, "Background scan(s) not found")
        raise HTTPException(status_code=404, detail="Backgroud scan(s) not found")
    
    # if back1.instrumentId == back2.instrumentId:
    #     markTaskWithErrorStatus(background.taskId,background.db,background.bearer,"Background scans must be from the same instrument")
    #     raise HTTPException(status_code=404, detail="Background scans must be from the same instrument")

    markTaskWithRunningStatus( background.taskId, background.db, background.bearer, "running")

    back = mediumBackground(back1, back2)

    print("back :",back)

    instrumentId = background.instrumentId
    projectId = background.projectId

    data = {
        # "url": f"http://localhost:8000/background/{back}",
        "url": back,
        # "instrumentId": instrumentId,
        # "projectId": projectId
        "taskId": background.taskId,
        "type":"MEDIUM_BACKGROUND"
    }

    print("background() :",data)

    # save_image(back, "/Users/sebastiengalvagno/Drives/Zooscan/Zooscan_dyfamed_wp2_2023_biotom_sn001/Zooscan_back/20230229_1219_background_large_manual.tif")

    #TODO Mettre dans une fonction car optionnel
    # response = requests.put(url=f"${dbserver.getUrl()}background/{instrumentId}/url?projectId=${projectId}", data=data, headers={"Authorization": f"Bearer {background.bearer}"})
    url = f"{dbserver.getUrl()}/background/{instrumentId}/url?projectId={projectId}"
    print("url:",url)
    response = requests.post(url=url, data=data, headers={"Authorization": f"Bearer {background.bearer}"})
    if response.ok:
        markTaskWithDoneStatus( background.taskId, background.db, background.bearer, response.json().get("id"))
        print(response.json())
        # return response.json().get("id")
        return response.json()
    else:
        print("response.status_code:",response.status_code)
        # if ( response.status_code == 405):
        markTaskWithErrorStatus( background.taskId, background.db, background.bearer, "Cannot add medium scan in the DB")
        detail = {
            "status": "partial_success",
            "file_url": back,
            "message": "Data generated successfully, but failed to add to the DB",
            "db_error": response.status_code,
            "taskId": background.taskId
        }
        # raise HTTPException(status_code=206, detail="Cannot add medium scan in the DB")
        raise HTTPException(status_code=206, detail=detail)
        # else:
        #     markTaskWithErrorStatus(background.taskId, background.db, background.bearer, "Cannot generate medium scan")
        #     raise HTTPException(status_code=response.status_code, detail="Cannot generate medium scan")


# from importe import importe

# importe(app)

class Project(BaseModel):
    """
        Project path: the path to the project folder
        bearer: the bearer token to use for the request
        db: the database to use for the request
        name: [optional] the name of the project else take the name of the project folder
        instrumentSerialNumber: [optional] the serial number of the instrument else instrument will marked undefine in the DB
    """
    path: str 
    bearer: Union[str, None] = None
    db: Union[str, None] = None
    name: Union[str, None] = None
    instrumentSerialNumber: Union[str, None] = None 

def testBearer(db,bearer):
    if (bearer == None or db == None): 
        print("markTaskWithRunningStatus: bearer or db is None")
        print("bearer: ", bearer)
        print("db: ", db)
        raise HTTPException(status_code=404, detail="Bearer or db is None")


def parse_meta_file(filepath):
    data = {}
    with open(filepath, 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.strip().split('=')
                # Clean up whitespace
                key = key.strip()
                value = value.strip()
                data[key] = value
    
    return data



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

def convertsamplekey(samplejson):

    # scanid;sampleid;scanop;fracid;fracmin;fracsup;fracnb;observation;code;submethod;cellpart;replicates;volini;volprec
    convertionkey = {
        'sampleid': 'sample_id', # 'apero2023_tha_bioness_sup2000_017_st66_d_n1', 
        'scanop': 'scanning_operator', # 'adelaide_perruchon',
        'ship': 'ship_name', # 'thalassa', 
        'scientificprog': 'scientific_program', # 'apero', 
        'stationid': 'station_id', # '66', 
        'date': 'sampling_date' , # '20230704-0503', 
        'latitude': 'latitude_start', # '51.5293', 
        'longitude': 'longitude_start', # '19.2159', 
        'depth': 'bottom_depth', # '99999', 
        'ctdref': 'ctd_reference', # 'apero_bio_ctd_017', 
        'otherref': 'other_reference', # 'apero_bio_uvp6_017u', 
        'townb': 'number_of_tow', # '1', 
        'towtype': 'tow_type', # '1', 
        'nettype': 'net_sampling_type', # 'bioness', 
        'netmesh': 'net_mesh', # '2000', 
        'netsurf': 'net_opening_surface', # '1', 
        'zmax': 'maximum_depth', # '1008', 
        'zmin': 'minimum_depth', # '820', 
        # 'Vol': '357', 
        # 'FracId': 'd1_1_sur_1', 
        'fracmin': 'fraction_min_mesh', # '10000', 
        'fracsup': 'fraction_max_mesh', # '999999', 
        'fracnb': 'fraction_number', # '1', 
        'observation': 'observation', # 'no', 
        # 'Code': '1', 
        # 'SubMethod': 'motoda', 
        # 'CellPart': '1', 
        # 'Replicates': '1', 
        # 'VolIni': '1', 
        # 'VolPrec': '1', 
        'sample_comment': 'sample_comment', #input_volume_including_on_board_fractioning__total_volume_is_714_mcube__counterpart_in_existing_project_bioness', 
        # 'vol_qc': '1', 
        'depth_qc': 'quality_flag_for_depth_measurement', # '1', 
        # 'sample_qc': '1111', 
        'barcode': 'barcode', # 'ape000000147', 
        'latitude_end': 'latitude_end', # '51.5214', 
        'longitude_end': 'longitude_end', # '19.2674', 
        'net_duration': 'sampling_duration', # '20', 
        'ship_speed_knots': 'ship_speed', # '2', 
        'cable_length': 'cable_length', # '9999', 
        'cable_angle': 'cable_angle_from_vertical', # '99999', 
        'cable_speed': 'cable_speed', # '0', 
        'nb_jar': 'number_of_jars' # '1'

        # jar_airtighness
        # sample_richness
        # sample_conditioning
        # sample_content
        # fraction_id_suffix
        # spliting_ratio
        # quality_flag_filtered_volume
        # 
    }

    # def condition(key):
    #     return key in convertionkey

    # def transform_key(key):
    #     return convertionkey[key]

    new_dict = {}

    def latlng_correction(value):
        try:
            val = float(value)
            degrees = int(val)
            decimal = (val - degrees) * 100
            decimal = round(decimal/30*50, 4)
            return degrees + decimal/100
        except ValueError:
            return value

    def latitude_correction(latitude):
        try:
            return latlng_correction(latitude)
        except ValueError:
            return latitude
    
    def longitude_correction(longitude):
        try:
            return - latlng_correction(longitude)
        except ValueError:
            return longitude

    for key, value in samplejson.items():
        if key in convertionkey:
            new_key = convertionkey[key]
            match key:
                case 'longitude':
                    new_value = longitude_correction(value)
                case 'longitude_end':
                    new_value = longitude_correction(value)
                case 'latitude':
                    new_value = latitude_correction(value)
                case 'latitude_end':
                    new_value = latitude_correction(value)
                case _:
                    new_value = value
            new_dict[new_key] = new_value
        else:
            new_dict[key] = value  # Keep the key unchanged
    return new_dict

def convertscankey(subsamplejson):

    # scanid;sampleid;scanop;fracid;fracmin;fracsup;fracnb;observation;code;submethod;cellpart;replicates;volini;volprec
    convertionkey = {
        # scanid        ;sampleid ;scanop   ;fracid ;fracmin ;fracsup ;fracnb ;observation ;code ;submethod ;cellpart ;replicates ;volini ;volprec
        'scanid':'scan_id',
        'sampleid':'sample_id',
        'scanop' : 'scanning_operator',
        'fracid':'frac_id', # ??
        'fracmin' :'fraction_min_mesh',
        'fracsup':'fraction_max_mesh',
        'fracnb':'fraction_number',
        'observation':'observation',
        'code' :'code', # ??
        'submethod':'submethod', # ??
        'cellpart':'cellpart', # ??
        'replicates': 'replicates', # ??
        'volini': 'volini', # ??
        'volprec':'volprec', # ??

    }
    new_dict = {}
    for key, value in subsamplejson.items():
        if key in convertionkey:
            new_key = convertionkey[key]
            new_dict[new_key] = value
        else:
            new_dict[key] = value  # Keep the key unchanged
    return new_dict

def parse_tsv(filepath: str) -> List[Dict[str, Any]]:
    """Parses a TSV file and returns a list of dictionaries."""

    data: List[Dict[str, Any]] = []
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as tsvfile:
            reader = csv.DictReader(tsvfile, delimiter=';')  # DictReader directly creates dictionaries
            for row in reader:
                cleaned_row = {} #Create a new dict for each row to store cleaned data
                for key, value in row.items(): #Iterate and clean each item
                    cleaned_row[key] = value.strip() if value else None #Clean whitespace. Handle empty values
                data.append(cleaned_row) # Add the cleaned row to the list
        return data

    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        return []  # Or raise the exception
    except Exception as e: # Catching other potential errors
        print(f"An error occurred during TSV parsing: {e}") 
        return []



def add_scans(image_path:str,projectid:str,sampleid:str,subsampleid:str,headers,db:str,user_id:str,instrument_id:str):

    print("add scans to subsample", subsampleid)

    body = {
        "url": image_path,
        "subsampleId": subsampleid,
        "userId": user_id,
        "type":"SCAN",
        "instrumentId": instrument_id
    }

    print("body:",body)
    # url = f"{db}scan/{instrument_id}/url"
    url = f"{db}scan/{subsampleid}/url"
    print("url:",url)

    response = requests.put(url, json=body, headers=headers)

    print("response: ", response)
    if response.status_code == 200:
        scan = response.json()
        print("scan: ", scan)

    else:

        raise HTTPException(status_code=response.status_code, detail="Error importing scan: " + response.text)




def transform_to_raw_string(input_str):
    parts = input_str.rsplit('_', 1)
    return f"{parts[0]}_raw_{parts[1]}"


def add_subsamples(path,data_scan:List[Dict[str, Any]],projectid:str,sampleid:str,db:str,bearer:str):

    print("add subsamples to sample", sampleid)

    for row in data_scan:
        print("---------------------------")
        print("Scan:",row)

        data_converted = convertscankey(row)
        print("converted:",data_converted)
        
        user_id = "658dd7ea24bc10a4bf1e37e2"
        instrument_id = "65c4e0994653afb2f69b11ce"

        body = {
            "name": row['scanid'], #"p12",
            "metadataModelId": "",
            "data": {
                "scan_id": data_converted['scan_id'], #"p11",
                "sample_id": data_converted['sample_id'], #1,
                "fraction_id": data_converted['frac_id'], #1
                "fraction_number": data_converted['fraction_number'], #1
                "scanning_operator": "seb", #data_converted['scanning_operator'], #TODO: get from user or create the missing user
                "observation": data_converted['observation'],
                "fraction_min_mesh": data_converted['fraction_min_mesh'],
                "fraction_max_mesh": data_converted['fraction_max_mesh'],
                "spliting_ratio": 1,
                "remark_on_fraction": "",
                "submethod": data_converted['submethod']
            },
            "user_id":user_id
        }

        url = f"{db}projects/{projectid}/samples/{sampleid}/subsamples"
        print("url: ", url)
        
        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json",
            # "X-Transaction-Id": transactionId
        }
 
        print("headers: ", headers)
        print("body: ", body)

        response = requests.post(url, json=body, headers=headers)

        print("response: ", response)
        if response.status_code == 200:
            subsample = response.json()
            print("subsample: ", subsample)

            
            scan_name = transform_to_raw_string(data_converted['scan_id']) + ".tif"
            print("scan_name: ", scan_name)

            image_path = Path(path,"Zooscan_scan","_raw",scan_name).absolute()
            print("image_path: ", image_path)

            if image_path.exists():
                print("image_path exists")
                add_scans(image_path.as_posix(),projectid,data_converted['sample_id'],subsample['id'],headers,db,user_id,instrument_id)
            else:
                print("image_path does not exist")
                continue



def addSamples(path:str, bearer, db, projectid:str):
    print("addSample")
    print("projectid: ", projectid)
    print("path: ", path)
    print("bearer: ", bearer)
    print("db: ", db)
    testBearer(db,bearer)

    path_sample = Path(path,"Zooscan_meta","zooscan_sample_header_table.csv")
    path_scan = Path(path,"Zooscan_meta","zooscan_scan_header_table.csv")

    print("path_sample: ", path_sample)
    print("path_scan: ", path_scan)

    data = parse_tsv(path_sample)
    data_scan = parse_tsv(path_scan)

    print("data:",data)

    if data:
        for row in data:
            # print("---------------------------")
            # print("Sample:",row)

            data_converted_sample = convertsamplekey(row)

            body = {
                "name" : data_converted_sample["sample_id"],
                "metadataModelId": "6565df171af7a84541c48b20",
                "data":data_converted_sample
            }
            # print("body_sample:", json.dumps(body, indent=2))

            url = f"{db}projects/{projectid}/samples"
            # print("url: ", url)
        
            headers = {
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/json",
                # "X-Transaction-Id": transactionId
            }

            # print("headers: ", headers)

            response = requests.post(url, json=body, headers=headers)

            # print("================================")
            # print("response:",response)
            # print("response:",response.status_code)

            if response.status_code == 200:
                sample = response.json()
                # print("sample", sample)
                # print("sample id:", sample['id'])

                # for row in data_scan:
                #     data_converted = convertscankey(row)
                #     print("data_scan:",row)
                #     print("data_scan converted:",data_converted)

                # print("Search sampleid: ", sample['name'] )
                # print("data_scan",data_scan)

                # vuescans = [s['scanid'] for s in data_scan ]#if s['sampleid'] == sample['sampleid']]
                # print("vuescans:",vuescans)
        

                # scnas = data_scan.map(s):s.sampleid==sample.sampleid
                subsamples = list(filter(lambda s: s['sampleid'] == sample['name'], data_scan))

                # print("***********************************************")
                # print("scans:", scans)



                if subsamples:
                    print("***********************************************")
                    print("subsamples:",subsamples)
                    add_subsamples(path,subsamples,projectid,sample['id'],db,bearer)
                    # add_scans(data_scan,projectid,sample.id,db,bearer)


            print("import done")




def addSamples_rawmethod(url, bearer, db, projectid:str):
    print("addSample")
    print("projectid: ", projectid)
    print("url: ", url)
    print("bearer: ", bearer)
    print("db: ", db)
    testBearer(db,bearer)

    path = Path(url,"Zooscan_scan","_raw")
    print("path: ", path)
    # meta_files = list(path.glob("*_meta.txt"))

    meta_files = []
    for root, dirs, files in os.walk(path):
        print("root: ", root)
        print("dirs: ", dirs)
        print("files: ", files)
        for file in files:
            if file.endswith("_meta.txt"):
                # filepath = os.path.join(root, file)
                filepath = Path(root, file)

                print("file:",filepath)

                # with filepath as metafile:
                #     print("metafile")

                #     for line in metafile:
                #         print(line)
                prefix = file.split('_meta.txt')[0]

                print("prefix: ", prefix)

                print("metafile: ", file)
                logfile = Path(path, prefix + "_log.txt")
                print("logfile: ", logfile)
                if not logfile.is_file(): 
                    print("logfile ", logfile, " not found")
                    pass
                
                rawfile = Path(path, prefix + "_raw.tif")
                print("rawfile: ", rawfile)
                if not logfile.is_file(): 
                    print("logfile ", rawfile, " not found")
                    pass

                meta_data = parse_meta_file(filepath)
                json_data = json.dumps(meta_data)
        
                # print("json_data: ", json.dumps(meta_data, indent=2))

                meta_files.append([filepath, logfile, rawfile, meta_data])



                print("----------------------------------")

    for file in meta_files:
        # print("file:",file)

        # print("sample data:",file[3])
        data = converted_sample = convertsamplekey(file[3])

        # print("sample data: ", json.dumps(data, indent=2))
        # print("sample_id: ", data["sample_id"])
        print("----------------------------------")

        # continue
        # print("meta_files: ", meta_files)
        # print("body_sample:",body_sample)

        body = {
            "name" : data["sample_id"],
            "metadataModelId": "6565df171af7a84541c48b20",
            "data":data
        }
        print("body_sample:", json.dumps(body, indent=2))

        url = f"{db}projects/${projectid}/samples"
        print("url: ", url)
    
        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json",
            # "X-Transaction-Id": transactionId
        }

        print("headers: ", headers)

        response = requests.post(url, json=body, headers=headers)

        print("import done")


# def BeginTransaction(db,bearer):
#     url = f"{db}transaction/begin"
#     print("url: ", url)

#     headers = {
#         "Authorization": f"Bearer {bearer}",
#         "Content-Type": "application/json"
#     }

#     response = requests.post(url, json={},headers=headers)

#     if response.status_code == 200:
#         print("response: ", response)
#         print("response text: ", response.text)
#         # transactionId = response.text
#         transactionId = json.loads(response.text)  # This removes the extra quotes
#         return transactionId
#     else:
#         raise HTTPException(status_code=response.status_code, detail="Error Cannot create a transaction")
# def RollBackTransaction(db,bearer,transactionId):
#     url = f"{db}transaction/rollback"
#     print("url: ", url)

#     headers = {
#         "Authorization": f"Bearer {bearer}",
#         "Content-Type": "application/json",
#         "X-Transaction-Id": transactionId
#     }

#     response = requests.post(url, json={},headers=headers)

#     if response.status_code in [200,204]:
#         print("response: ", response)
#         # print("response text: ", response.text)
#         print("Transaction cancelled")
#     else:
#         raise HTTPException(status_code=response.status_code, detail="Error Cannot RollBack the transaction: " + transactionId)
# def CommitTransaction(db,bearer,transactionId):
#     url = f"{db}transaction/commit"
#     print("url: ", url)

#     headers = {
#         "Authorization": f"Bearer {bearer}",
#         "Content-Type": "application/json",
#         "X-Transaction-Id": transactionId
#     }

#     response = requests.post(url, json={},headers=headers)

#     if response.status_code in [200,204]:
#         print("response: ", response)
#         print("response text: ", response.text)
#         print("Transaction commited")
#     else:
#         raise HTTPException(status_code=response.status_code, detail="Error Cannot commit the transaction: " + transactionId)

# with transaction
# @app.post("/import")
# def import_project(project:Project):

#     print("import project", project.path )
#     print("import project", project.bearer )
#     print("import project", project.db )
#     testBearer(project.db,project.bearer)
#     # if (project.bearer == None or project.db == None): 
#     #     print("markTaskWithRunningStatus: bearer or db is None")
#     #     # print("bearer: ", bearer)
#     #     # print("db: ", db)
#     #     return HTTPException(status_code=404, detail="Bearer or db is None")
#     #     return envoie un json avec plus d'infos mais pas le status code dans le header

#     transactionId  = BeginTransaction(project.db,project.bearer)
#     print("transactionId: ", transactionId)

#     # url = f"{dbserver.getUrl()}/projects"
#     url = f"{project.db}projects"
#     print("url: ", url)

#     body = {  
#         # "project_id": "null",
#         "name": 'SebProjectFromHappy',
#         # "thematic": "null",
#         "driveId": '65bd147e3ee6f56bc8737879',
#         "instrumentId": '65c4e0e44653afb2f69b11d1',
#         "acronym": 'acronym',
#         "description": 'dyfamed',
#         "ecotaxa_project_name": 'ecotaxa project name',
#         "ecotaxa_project_title": 'ecotaxa_project_title',
#         "ecotaxa_project": 1234,
#         "scanningOptions": 'LARGE',
#         "density": '2400'
#     }
    
#     headers = {
#         "Authorization": f"Bearer {project.bearer}",
#         "Content-Type": "application/json",
#         "X-Transaction-Id": transactionId
#     }

#     print("headers: ", headers)

#     response = requests.post(url, json=body, headers=headers)


#     if response.status_code != 204:
#         print("import project response: ", response)
#         print("response text: ", response.text)
#         try :
#             # RollBackTransaction(project.db, project.bearer, transactionId)
#             raise HTTPException(status_code=response.status_code, detail="Error importing project: " + response.text)
#         except:
#             print("Error RollBackTransaction")
#             raise HTTPException(status_code=response.status_code, detail="Error importing project: " + response.text)

#     print("response: ", response)
#     print("response: ", response.status_code)
          
#     projectid = response.json().get("id")


#     addSamples(project.path, project.bearer, project.db, projectid)


#     # CommitTransaction(project.db, project.bearer, transactionId)
    
#     return response.json()




# def post_project(db,bearer,transactionId):
        
#     url = f"{db}projects"
#     print("url: ", url)
    
#     body = {  
#     # "project_id": "null",
#     "name": 'SebProjectFromHappy',
#     # "thematic": "null",
#     "driveId": '65bd147e3ee6f56bc8737879',
#     "instrumentId": '65c4e0e44653afb2f69b11d1',
#     "acronym": 'acronym',
#     "description": 'dyfamed',
#     "ecotaxa_project_name": 'ecotaxa project name',
#     "ecotaxa_project_title": 'ecotaxa_project_title',
#     "ecotaxa_project": 1234,
#     "scanningOptions": 'LARGE',
#     "density": '2400'
#     }
    
#     headers = {
#         "Authorization": f"Bearer {bearer}",
#         "Content-Type": "application/json",
#         "X-Transaction-Id": transactionId
#     }

#     print("headers: ", headers)

#     response = requests.post(url, json=body, headers=headers)
#     print("import project response: ", response)
#     print("response text: ", response.text)

def getInstrumentFromSN(db,bearer,instrumentSN):
    url = f"{db}instruments"
    print("url: ", url)
    
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json",
    }
    print("headers: ", headers)
    response = requests.get(url, headers=headers)
    print("response: ", response)
    if response.status_code == 200:
        instruments = response.json()
        print("instruments: ", instruments)
        for instrument in instruments:
            if instrument["sn"] == instrumentSN:
                return instrument
    return None

@app.post("/import")
def import_project(project:Project):

    print("import project path", project.path)
    print("import project bearer", project.bearer)
    print("import project db", project.db)
    testBearer(project.db, project.bearer)

    if Path(project.path).exists() == False:
        raise HTTPException(status_code=404, detail=f"Project path '{project.path}' does not exist")

    projectname = project.name if project.name != None else Path(project.path).name
    instrumentSN = project.instrumentSerialNumber
    if instrumentSN != None:
        instrument = getInstrumentFromSN(project.db, project.bearer, instrumentSN)
    # if (project.bearer == None or project.db == None):
    #     print("markTaskWithRunningStatus: bearer or db is None")
    #     # print("bearer: ", bearer)
    #     # print("db: ", db)
    #     return HTTPException(status_code=404, detail="Bearer or db is None")
    #     return envoie un json avec plus d'infos mais pas le status code dans le header

    # url = f"{dbserver.getUrl()}/projects"
    url = f"{project.db}projects"
    print("url: ", url)

    body = {
        # "name": 'SebProjectFromHappy',
        "name" : projectname,
        "driveId": '65bd147e3ee6f56bc8737879',
        "instrumentId": '65c4e0e44653afb2f69b11d1',
        "acronym": 'acronym',
        "description": 'dyfamed',
        "ecotaxa_project_name": 'ecotaxa project name',
        "ecotaxa_project_title": 'ecotaxa_project_title',
        "ecotaxa_project": 1234,
        "scanningOptions": 'LARGE',
        "density": '2400'
    }
    
    headers = {
        "Authorization": f"Bearer {project.bearer}",
        "Content-Type": "application/json",
        # "X-Transaction-Id": transactionId
    }

    print("headers: ", headers)
    response = requests.post(url, json=body, headers=headers)
    if response.status_code != 200:
        if response.status_code == 409:
            print("project already exists")
            if projectname:
                url = f"{project.db}projects/{projectname}?name"
                print("url: ", url)
        #       response = requests.get(url, headers=headers)
        #       if response.status_code != 200:
                # raise HTTPException(status_code=response.status_code, detail="Error importing project (1): " + response.text)
        # else:
        #     print("import project response: ", response)
        #     print("response text: ", response.text)
        #     # try :
        #     # RollBackTransaction(project.db, project.bearer, transactionId)
            raise HTTPException(status_code=response.status_code, detail="Error importing project: " + response.text)
            # raise HTTPException(status_code=response.status_code, detail="Error importing project (2): " + response.text)

    print("response: ", response)
    print("response: ", response.status_code)  
    projectid = response.json().get("id")


    addSamples(project.path, project.bearer, project.db, projectid)


    # CommitTransaction(project.db, project.bearer, transactionId)
    
    return response.json()

# @app.post("/test_transaction")
# def test_transaction(project:Project):
#     transactionId = BeginTransaction(project.db,project.bearer)
#     print("transactionId: ", transactionId)
#     # post_project(project.db,project.bearer,transactionId)
#     CommitTransaction(project.db,project.bearer,transactionId)
#     return {"message": "Transaction committed"}
