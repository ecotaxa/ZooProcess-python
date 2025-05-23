
import requests
from .img_tools import getPath, saveimage, mkdir, loadimage, image_info, rename
from .debug_tools import dump_structure
import cv2
import numpy as np


from .server import Server 

# server = "http://niko.obs-vlfr.fr:5000"
# server2 = "http://localhost:5001"
# dbserver = "http://zooprocess.imev-mer.fr:8081/v1/"





server = Server("http://niko.obs-vlfr.fr:5000", "/")
server = Server("http://seb:5000", "/")
server2 = Server("http://localhost:5001", "/")
dbserver = Server("http://zooprocess.imev-mer.fr:8081/v1/", "/ping")


# def test_server():
#     result = requests.get(server)

#     if result.status_code != 200:
#         raise Exception("Server not responding")
    

def send_img_to_separator(filename, out_path=None):

    with open(filename, "rb") as imageData:


       
        file_dict = {
            "image": imageData,
            "type": "image/jpeg"
        }

        base_url = server
        path = "/v2/models/multi_plankton_separation/predict/"
        params = "?model=default_mask_multi_plankton&min_mask_score=0.9&min_mask_value=0.5&accept=image%2Fpng"

        url = base_url.getUrl() + path + params

        headers = {
            'accept': 'image/png',
            # 'Content-Type': 'multipart/form-data'
        }

        print("Request")
        print("url: ", url)
        print("headers: ", headers)
        print("files: ",file_dict)

        response = requests.post(url, files=file_dict, headers=headers)
        print (response)

        return response



def separate_img(path,filename,path_out, taskId=None, bearer=None, db=None):

    fullfilename = path + filename

    response = send_img_to_separator(fullfilename)
    if response.ok:
        img = response.content

        mask_img = getPath(filename, extraname="mask", ext="png", path=path_out)
        print ("mask file" , mask_img)

        with open(mask_img, "wb") as f:
            f.write(response.content)


        if taskId != None :
            data = {
                'url':mask_img,
                'type':'mask'
            }
            print(f"Post to DB: {dbserver.getUrl()}separator/{taskId} < {data}")
            if ( db != None and bearer != None ):
                requests.put(url=f"${dbserver.getUrl()}separator/{taskId}", data=data, headers={"Authorization": f"Bearer {bearer}"})

        return mask_img
    
    else:
        print ( response.raise_for_status() )
        return None



def separate_apply_mask(filename_image, filename_mask) -> np.ndarray :

    img = loadimage(filename_image)
    mask = loadimage(filename_mask) 

    mask = cv2.bitwise_not(mask)
    fg = cv2.bitwise_or(img, img, mask=mask)
    
    background = np.full(img.shape, 255, dtype=np.uint8)
    mask = cv2.bitwise_not(mask)
    bk = cv2.bitwise_or(background, background, mask=mask)

    final = cv2.bitwise_or(fg, bk)
    return final


def separate_images(path, path_out, path_result, db=None, bearer=None, taskId=None) -> list:

    import pathlib
    import glob
    import os

    print(" in: ", path)
    print("out: ", path_out)


    regex = f"{path}*.jpg"
    print ("regex: ", regex)

    images = []

    if taskId != None:          
        data = {
            'url' : img_dst,
            'type': 'merge'
        }
        print(f"Post to DB: {dbserver.getUrl()}separator/{taskId} < {data}")
        requests.put(url=f"${dbserver.getUrl()}separator/{taskId}", data=data, headers={"Authorization": f"Bearer {bearer}"})

    files = glob.glob(regex)
    for file in files: 
        decompose = os.path.split(file)
        name = decompose[1]
        mask_img = separate_img(path, name, path_out, db=db, taskId=taskId, bearer=bearer)
        print("mask: ", mask_img)

        img_src = path  + name
        img = separate_apply_mask(img_src, mask_img)

        img_dst = path_result + name
        saveimage(img, img_dst)
        print("image merged: ", img_dst)

        # taskId = 1 
        if taskId != None:          
            data = {
                'url' : img_dst,
                'type': 'merge'
            }
            print(f"Post to DB: {dbserver.getUrl()}separator/{taskId} < {data}")
            requests.put(url=f"${dbserver.getUrl()}separator/{taskId}", data=data, headers={"Authorization": f"Bearer {bearer}"})
        # else:
        #     print("AAAAARRRRRRGGGGGHHHHHH !!!!!!!!")

        images.append(img_dst)
                       
    return images


# # rendre cette fonction asynchrone
# def separate_images(path, path_out, path_result, db):

#     import pathlib
#     import glob
#     import os

#     print(" in: ", path)
#     print("out: ", path_out)

#     test_server()

#     regex = f"{path}*.jpg"
#     print ("regex: ", regex)

#     images = []

#     files = glob.glob(regex)
#     for file in files: 
#         decompose = os.path.split(file)
#         name = decompose[1]
#         mask_img = separate_img(path, name, path_out)
#         print("mask: ", mask_img)

#         img_src = path + name
#         img = separate_apply_mask(img_src, mask_img)

#         img_dst = path_result + name
#         saveimage(img, img_dst)
#         print("image merged: ", img_dst)

#         images.append(img_dst)

#         #put(f"/sperator/{id}/", img_dst)

                       
#     return images




def getFolder(scanId):

    # resquests.
    pass


def separate_multiple(scanId,bearer):

    print("separate multiple scanId: ", scanId)

    multiples = getFolder(scanId)
   