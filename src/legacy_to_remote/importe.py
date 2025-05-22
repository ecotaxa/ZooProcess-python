# import old zooscan project

import os
import requests
import csv
from typing import List, Dict, Any
import re
import json

from fastapi import HTTPException
from pathlib import Path

from Models import Project
from remote.connection import testBearer
from remote.request import getInstrumentFromSN, getDriveId

from remote.DB import DB


def convertsamplekey(samplejson):

    # scanid;sampleid;scanop;fracid;fracmin;fracsup;fracnb;observation;code;submethod;cellpart;replicates;volini;volprec
    convertionkey = {
        "sampleid": "sample_id",  # 'apero2023_tha_bioness_sup2000_017_st66_d_n1',
        "scanop": "scanning_operator",  # 'adelaide_perruchon',
        "ship": "ship_name",  # 'thalassa',
        "scientificprog": "scientific_program",  # 'apero',
        "stationid": "station_id",  # '66',
        # 'date': 'sampling_date' , # '20230704-0503',
        "createdAt": "sampling_date",  # '20230704-0503',
        "latitude": "latitude_start",  # '51.5293',
        "longitude": "longitude_start",  # '19.2159',
        "depth": "bottom_depth",  # '99999',
        "ctdref": "ctd_reference",  # 'apero_bio_ctd_017',
        "otherref": "other_reference",  # 'apero_bio_uvp6_017u',
        "townb": "number_of_tow",  # '1',
        "towtype": "tow_type",  # '1',
        "nettype": "net_sampling_type",  # 'bioness',
        "netmesh": "net_mesh",  # '2000',
        "netsurf": "net_opening_surface",  # '1',
        "zmax": "maximum_depth",  # '1008',
        "zmin": "minimum_depth",  # '820',
        # 'Vol': '357',
        # 'FracId': 'd1_1_sur_1',
        "fracmin": "fraction_min_mesh",  # '10000',
        "fracsup": "fraction_max_mesh",  # '999999',
        "fracnb": "fraction_number",  # '1',
        "observation": "observation",  # 'no',
        # 'Code': '1',
        # 'SubMethod': 'motoda',
        # 'CellPart': '1',
        # 'Replicates': '1',
        # 'VolIni': '1',
        # 'VolPrec': '1',
        "sample_comment": "sample_comment",  # input_volume_including_on_board_fractioning__total_volume_is_714_mcube__counterpart_in_existing_project_bioness',
        # 'vol_qc': '1',
        "depth_qc": "quality_flag_for_depth_measurement",  # '1',
        # 'sample_qc': '1111',
        "barcode": "barcode",  # 'ape000000147',
        "latitude_end": "latitude_end",  # '51.5214',
        "longitude_end": "longitude_end",  # '19.2674',
        "net_duration": "sampling_duration",  # '20',
        "ship_speed_knots": "ship_speed",  # '2',
        "cable_length": "cable_length",  # '9999',
        "cable_angle": "cable_angle_from_vertical",  # '99999',
        "cable_speed": "cable_speed",  # '0',
        "nb_jar": "number_of_jars",  # '1'
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
            decimal = round(decimal / 30 * 50, 4)
            return degrees + decimal / 100
        except ValueError:
            return value

    def latitude_correction(latitude):
        try:
            return latlng_correction(latitude)
        except ValueError:
            return latitude

    def longitude_correction(longitude):
        try:
            return -latlng_correction(longitude)
        except ValueError:
            return longitude

    # for key, value in samplejson.items():
    #     if key in convertionkey:
    #         new_key = convertionkey[key]
    #         match (key):
    #             case 'longitude':
    #                 new_value = longitude_correction(value)
    #             case 'longitude_end':
    #                 new_value = longitude_correction(value)
    #             case 'latitude':
    #                 new_value = latitude_correction(value)
    #             case 'latitude_end':
    #                 new_value = latitude_correction(value)
    #             case _:
    #                 new_value = value
    #         new_dict[new_key] = new_value
    #     else:
    #         new_dict[key] = value  # Keep the key unchanged
    # return new_dict
    # match not supported  in 3.13.3 ???
    for key, value in samplejson.items():
        if key in convertionkey:
            new_key = convertionkey[key]
            if key == "longitude":
                new_value = longitude_correction(value)
            elif key == "longitude_end":
                new_value = longitude_correction(value)
            elif key == "latitude":
                new_value = latitude_correction(value)
            elif key == "latitude_end":
                new_value = latitude_correction(value)
            else:
                new_value = value
            new_dict[new_key] = new_value
        else:
            new_dict[key] = value  # Keep the key unchanged
    return new_dict


def parse_tsv(filepath: str) -> List[Dict[str, Any]]:
    """Parses a TSV file and returns a list of dictionaries."""

    data: List[Dict[str, Any]] = []
    try:
        with open(filepath, "r", newline="", encoding="utf-8") as tsvfile:
            reader = csv.DictReader(
                tsvfile, delimiter=";"
            )  # DictReader directly creates dictionaries
            for row in reader:
                cleaned_row = {}  # Create a new dict for each row to store cleaned data
                for key, value in row.items():  # Iterate and clean each item
                    cleaned_row[key] = (
                        value.strip() if value else None
                    )  # Clean whitespace. Handle empty values
                data.append(cleaned_row)  # Add the cleaned row to the list
        return data

    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        return []  # Or raise the exception
    except Exception as e:  # Catching other potential errors
        print(f"An error occurred during TSV parsing: {e}")
        return []


def transform_to_raw_string(input_str):
    parts = input_str.rsplit("_", 1)
    return f"{parts[0]}_raw_{parts[1]}"


def convertscankey(subsamplejson):

    # scanid;sampleid;scanop;fracid;fracmin;fracsup;fracnb;observation;code;submethod;cellpart;replicates;volini;volprec
    convertionkey = {
        # scanid        ;sampleid ;scanop   ;fracid ;fracmin ;fracsup ;fracnb ;observation ;code ;submethod ;cellpart ;replicates ;volini ;volprec
        "scanid": "scan_id",
        "sampleid": "sample_id",
        "scanop": "scanning_operator",
        "fracid": "frac_id",  # ??
        "fracmin": "fraction_min_mesh",
        "fracsup": "fraction_max_mesh",
        "fracnb": "fraction_number",
        "observation": "observation",
        "code": "code",  # ??
        "submethod": "submethod",  # ??
        "cellpart": "cellpart",  # ??
        "replicates": "replicates",  # ??
        "volini": "volini",  # ??
        "volprec": "volprec",  # ??
    }
    new_dict = {}
    for key, value in subsamplejson.items():
        if key in convertionkey:
            new_key = convertionkey[key]
            new_dict[new_key] = value
        else:
            new_dict[key] = value  # Keep the key unchanged
    return new_dict


def add_scans(
    image_path: str,
    projectid: str,
    sampleid: str,
    subsampleid: str,
    headers,
    db: str,
    user_id: str,
    instrument_id: str,
    type: str = "SCAN",
):

    print("add scans to subsample", subsampleid)

    body = {
        "url": image_path,
        "subsampleId": subsampleid,
        "userId": user_id,
        "type": type,
        "instrumentId": instrument_id,
    }

    print("body:", body)
    # url = f"{db}scan/{instrument_id}/url"
    url = f"{db}scan/{subsampleid}/url"
    print("url:", url)

    response = requests.put(url, json=body, headers=headers)

    print("response: ", response)
    if response.status_code == 200:
        scan = response.json()
        print("scan: ", scan)

    else:

        raise HTTPException(
            status_code=response.status_code,
            detail="Error importing scan: " + response.text,
        )


def listWorkFolders(path):
    """
    list all the folders from the path folder
    """
    # List all folders in the specified path
    folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    return folders


def convert_workpid2json(path):
    json_data = pid2json(path)

    # print("json: ", json_data)
    json_filepath = str(path).replace(".pid", ".json")
    # Save to JSON file
    with open(json_filepath, "w") as f:
        json.dump(json_data, f, indent=4)
    return json_filepath


def workpid2json(path, save=False):
    """
    convert a workpid file to json
    """
    json_data = pid2json(path)

    # print("json: ", json_data)
    # Save to JSON file
    if save:
        json_filepath = str(path).replace(".pid", ".json")
        with open(json_filepath, "w") as f:
            json.dump(json_data, f, indent=4)
    return json_filepath


def getDat1Path(path):
    """
    reurn path of the dat1.pid file
    """
    folder = Path(path).name
    pid_path = Path(path, folder + "_dat1.pid")
    print("pid_path:", pid_path)
    return pid_path


def addVignettesFromSample(path, folder, db: DB, projectId):
    """
    get vignette data from sample and add them to the DB
    to finish
    """

    # pid_path = Path(path, "Zooscan_scan", "_work", folder, folder + "_dat1.pid")
    pid_path = Path(path, folder, folder + "_dat1.pid")
    print("pid_path:", pid_path)
    json_filepath = convert_workpid2json(pid_path)
    print("json_filepath:", json_filepath)

    # Read the JSON file
    with open(json_filepath, "r") as f:
        data = json.load(f)

        # Extract the data array
        background_correct_using = data["Image_Process"]["Background_correct_using"]
        print("background_correct_using:", background_correct_using)
        image = data["Image_Process"]["Image"]
        print("image:", image)


def addVignettes(path, db: DB, projectId):
    """
    parse _work folder and add the vignettes to the DB
    """
    print("path:", path)

    path_work = Path(path, "Zooscan_scan", "_work")
    print("path_work:", path_work)
    # List all folders in the specified path
    folders = listWorkFolders(path_work)

    for folder in folders:
        print("folder:", folder)
        addVignettesFromSample(path, folder, db, projectId)


def extract_background_info(log_file_path):
    with open(log_file_path, "r") as f:
        content = f.read()
        match = re.search(r"Background_correct_using=\s*(.+)", content)
        return match.group(1).strip() if match else None


def pid2json(pid_filepath: str) -> dict:
    """
    Converts a .pid file into a structured JSON with sections, including data array of objects
    """
    result = {}
    current_section = None

    with open(pid_filepath, "r") as f:
        lines = f.readlines()

    if not lines[0].strip().upper() == "PID":
        raise ValueError("Not a valid PID file")

    lines = lines[1:]
    data_header = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line == "[Data]":  # Changed to match exact case
            current_section = "Data"
            result[current_section] = []  # Initialize as empty array
            continue

        if line == "[Image]":
            current_section = "image"
            result[current_section] = {}
            continue

        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            result[current_section] = {}
            continue

        if current_section == "Data":  # Changed to match case
            if line.startswith("!"):
                data_header = line[1:].strip().split(";")
            elif data_header and ";" in line:
                values = line.strip().split(";")
                data_object = {}
                for header, value in zip(data_header, values):
                    if value.replace(".", "", 1).replace("-", "", 1).isdigit():
                        data_object[header] = (
                            float(value) if "." in value else int(value)
                        )
                    else:
                        data_object[header] = value
                result["Data"].append(data_object)
        elif "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if current_section:
                result[current_section][key] = value

    return result


users: dict[str, str] = {}


def add_subsamples(
    path,
    data_scan: List[Dict[str, Any]],
    projectid: str,
    sampleid: str,
    db: str,
    bearer: str,
    instrumentId: str,
):
    """
    add the subsample in other words the scan
    """

    print("add subsamples to sample", sampleid)

    for row in data_scan:
        print("---------------------------")
        print("Scan:", row)

        data_converted = convertscankey(row)
        print("converted:", data_converted)

        # user_id = "658dd7ea24bc10a4bf1e37e2"
        user_id = None
        if data_converted["scanning_operator"] in users:
            user_id = users[data_converted["scanning_operator"]]

        # instrumentId = "65c4e0994653afb2f69b11ce" # TODO: remove this line

        body = {
            "name": row["scanid"],  # "p12",
            "metadataModelId": "",
            "data": {
                "scan_id": data_converted["scan_id"],  # "p11",
                "sample_id": data_converted["sample_id"],  # 1,
                "fraction_id": data_converted["frac_id"],  # 1
                "fraction_number": data_converted["fraction_number"],  # 1
                # "scanning_operator": "seb"
                "scanning_operator": data_converted[
                    "scanning_operator"
                ],  # TODO: get from user or create the missing user
                "observation": data_converted["observation"],
                "fraction_min_mesh": data_converted["fraction_min_mesh"],
                "fraction_max_mesh": data_converted["fraction_max_mesh"],
                "spliting_ratio": 1,
                "remark_on_fraction": "",
                "submethod": data_converted["submethod"],
            },
            # "user_id":user_id
        }

        if user_id:
            print("use user_id cached")
            body["user_id"] = user_id

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

            # add user_id to the cache
            if not user_id:
                users[data_converted["scanning_operator"]] = subsample["userId"]

            scan_name = transform_to_raw_string(data_converted["scan_id"]) + ".tif"
            print("scan_name: ", scan_name)

            image_path = Path(path, "Zooscan_scan", "_raw", scan_name).absolute()
            print("image_path: ", image_path)

            if image_path.exists():
                print("image_path exists")
                add_scans(
                    image_path.as_posix(),
                    projectid,
                    data_converted["sample_id"],
                    subsample["id"],
                    headers,
                    db,
                    subsample["userId"],
                    instrumentId,
                )
            else:
                print("image_path does not exist")
                continue


# list_backgrounds : Dict = {}


def list_background(background_path: str) -> Dict:
    """Lists all background files in the given directory and groups them by date prefix"""
    result = {}

    for file in os.listdir(background_path):
        if os.path.isfile(os.path.join(background_path, file)) and not file.startswith(
            "."
        ):
            parts = file.split("_back_", 1)
            if len(parts) == 2:
                prefix = parts[0]
                suffix = "back_" + parts[1]

                if prefix not in result:
                    result[prefix] = {}

                result[prefix][suffix] = file
            else:
                print("not _back_ segment in file")
                parts = file.split("_background_", 1)
                if len(parts) == 2:
                    prefix = parts[0]
                    if prefix not in result:
                        result[prefix] = {}
                    result[prefix]["background"] = file

    return result


def addSamples(path: str, bearer, db, projectid: str, instrumentId: str):
    print("addSample")
    print("projectid: ", projectid)
    print("path: ", path)
    print("bearer: ", bearer)
    print("db: ", db)
    testBearer(db, bearer)

    path_sample = Path(path, "Zooscan_meta", "zooscan_sample_header_table.csv")
    path_scan = Path(path, "Zooscan_meta", "zooscan_scan_header_table.csv")
    # path_background = Path(path,"Zooscan_back")

    print("path_sample: ", path_sample)
    print("path_scan: ", path_scan)

    data = parse_tsv(path_sample)
    data_scan = parse_tsv(path_scan)
    # list_backgrounds = list_background(path_background)

    print("data:", data)

    if data:
        for row in data:
            # print("---------------------------")
            # print("Sample:",row)

            data_converted_sample = convertsamplekey(row)

            # TODO: verify if data is compatible with metadataModelId, to do on the API server

            body = {
                "name": data_converted_sample["sample_id"],
                "metadataModelId": "6565df171af7a84541c48b20",
                "data": data_converted_sample,
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
                subsamples = list(
                    filter(lambda s: s["sampleid"] == sample["name"], data_scan)
                )

                # print("***********************************************")
                # print("scans:", scans)

                if subsamples:
                    print("***********************************************")
                    print("subsamples:", subsamples)
                    add_subsamples(
                        path,
                        subsamples,
                        projectid,
                        sample["id"],
                        db,
                        bearer,
                        instrumentId,
                    )
                    # add_scans(data_scan,projectid,sample.id,db,bearer)

            print("import done")


scanType: dict[str, str] = {
    "back_large_1.tif": "BACKGROUND",
    "back_large_2.tif": "BACKGROUND",
    "back_large_raw_1.tif": "RAW_BACKGROUND",
    "back_large_raw_2.tif": "RAW_BACKGROUND",
    "background": "MEDIUM_BACKGROUND",
}


def addBackground(
    path: str, bearer, db, projectid: str, instrumentid: str, userid: str
):
    print("addBackground")

    path_background = Path(path, "Zooscan_back")

    list_backgrounds = list_background(path_background)
    print("list_backgrounds:", list_backgrounds)

    for prefix, files in list_backgrounds.items():
        print("prefix:", prefix)
        print("files:", files)

        # if prefix == "back_large_manual_log.txt": continue

        # http://zooprocess.imev-mer.fr:8081/v1/scan/:instrumentId/url
        for file in files:

            print("file type:", file)
            print("file name:", files[file])

            if file == "back_large_manual_log.txt":
                continue

            url = Path(path_background, files[file]).as_posix()
            print("url:", url)
            type = scanType[file]
            print("type:", type)

            body = {
                "url": url,
                # "subsampleId": subsampleid,
                "projectId": projectid,
                "userId": userid,
                "type": type,
                "instrumentId": instrumentid,
            }
            print("body: ", body)

            headers = {
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/json",
                # "X-Transaction-Id": transactionId
            }
            print("headers: ", headers)

            # url = f"{db}scan/{instrument_id}/url"
            # url = f"{db}scan/{subsampleid}/url"
            url = f"{db}scan/*/url"
            print("url:", url)

            # continue

            response = requests.put(url, json=body, headers=headers)

            print("response: ", response)
            if response.status_code == 200:
                scan = response.json()
                print("scan: ", scan)

            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Error importing scan: " + response.text,
                )


def searchPidFile(path: str) -> str:
    print("search_pid_file")
    print("path: ", path)
    work_path = Path(path, "Zooscan_scan", "_work")
    print("work_path: ", work_path)

    # Get first directory in work_path
    first_dir = next(work_path.iterdir())

    # Find first .pid file
    for file in first_dir.iterdir():
        if file.suffix == ".pid":
            return str(file)

    return None


def import_old_project(project: Project):
    """
    Import a project made with legacy zooprocess
    """
    # print("import_old_project")
    # print("project: ", project)

    db = DB(db=project.db, bearer=project.bearer)

    print("import project path", project.path)
    print("import project bearer", project.bearer)
    print("import project db", project.db)
    testBearer(project.db, project.bearer)

    if Path(project.path).exists() == False:
        raise HTTPException(
            status_code=404, detail=f"Project path '{project.path}' does not exist"
        )

    projectname = project.name if project.name != None else Path(project.path).name
    driveName = (
        project.drive if project.drive != None else Path(project.path).parent.name
    )

    driveId = getDriveId(db, driveName)
    print("driveId: ", driveId)
    if driveId == None:
        raise HTTPException(
            status_code=404, detail=f"Drive '{driveName}' does not exist"
        )

    # instrumentSN = project.instrumentSerialNumber
    if project.instrumentSerialNumber != None:
        # instrument = getInstrumentFromSN(project.db, project.bearer, instrumentSN)
        instrument = getInstrumentFromSN(db, project.instrumentSerialNumber)
        print("instrument: ", instrument)
    # else:
    if instrument == None:
        # need to read a PID file to determine the instrument
        # pidfile = searchPidFile(project.path)

        # piddata = pid2json(pidfile)
        # PID the project does not contain inforation about the instrument
        # then user need to give the instrument serial number or create it before import
        raise HTTPException(
            status_code=404,
            detail="Instrument serial number not found. You need to create the instrument before import",
        )

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
        "name": projectname,
        "driveId": driveId,  #'65bd147e3ee6f56bc8737879',
        "instrumentId": instrument["id"],  #'65c4e0e44653afb2f69b11d1',
        # "acronym": 'acronym',
        # "description": 'dyfamed',
        # "ecotaxa_project_name": 'ecotaxa project name',
        # "ecotaxa_project_title": 'ecotaxa_project_title',
        # "ecotaxa_project": 1234,
        "scanningOptions": "LARGE",
        "density": "2400",
    }

    if project.acronym != None:
        body["acronym"] = project.acronym

    if project.description != None:
        body["description"] = project.description

    if project.ecotaxaProjectID != None:
        body["ecotaxa_project"] = project.ecotaxaProjectID
        # TODO request ecotaxa project to fill the name and the title, but need to know the credential, can ask to zooprocess API, but not sure it's relevant to do here
        # body["ecotaxa_project_name"] = "ecotaxa_project_name"
        # body["ecotaxa_project_title"] = "ecotaxa_project_title"

    print("body: ", body)

    # load a PID file
    pidfile = searchPidFile(project.path)

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
            raise HTTPException(
                status_code=response.status_code,
                detail="Error importing project: " + response.text,
            )
            # raise HTTPException(status_code=response.status_code, detail="Error importing project (2): " + response.text)

    print("response: ", response)
    print("response: ", response.status_code)
    imported_project = response.json()
    projectid = response.json().get("id")

    # path_background = Path(project.path,"Zooscan_back")
    # list_backgrounds = list_background(path_background)

    addSamples(project.path, project.bearer, project.db, projectid, instrument["id"])

    addBackground(
        project.path,
        project.bearer,
        project.db,
        projectid,
        instrumentid=instrument["id"],
        userid="toto",
    )

    # addVignettes(project.path, project.bearer, project.db, projectid)

    # CommitTransaction(project.db, project.bearer, transactionId)

    return response.json()
