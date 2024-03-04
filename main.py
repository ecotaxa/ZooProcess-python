from typing import Union

from src.separate import separate_images
from src.tools import mkdir

# from fastapi import FastAPI
from fastapi import FastAPI, HTTPException

import requests

app = FastAPI()


@app.get("/")
def read_root():
    return {
        "message": "Happy Pipeline",
        "description": "API to separate multiple plankton organisms from Zooprocess images"
        }


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}


from pydantic import BaseModel

# class Item(BaseModel):
#     name: str
#     price: float
#     is_offer: Union[bool, None] = None

# @app.put("/items/{item_id}")
# def update_item(item_id: int, item: Item):
#     return {"item_name": item.name, "item_id": item_id}


class Folder(BaseModel):
    path: str

@app.put("/separate/")
def separate(folder: Folder):
    import os
    #id = 1

    if os.path.isdir(folder.path):
        print("folder: ", folder.path)
        # return {"folder":folder.path}

        dest = "folder"

        id = requests.post("/separator/", json={"folder":folder.path}).json()["id"]
        # id = 1
        print("id: ", id)
        mask_folder = f"{folder.path}/mask"
        result_folder = f"{folder.path}/result"

        mkdir(dest)

        images = separate_images(path=folder.path, path_out=mask_folder, path_result=result_folder, db=id)

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



