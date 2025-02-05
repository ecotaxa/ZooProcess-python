# import zooprocess project using the tsv
# but it is not the good manner after talk with Marc

import json
import os
from pathlib import Path
import requests

from importe import convertsamplekey
from src.connection import testBearer


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
