from .DB import DB


# def getInstrumentFromSN(db,bearer,instrumentSN):
# url = f"{db}instruments"
# print("url: ", url)

# headers = {
#     "Authorization": f"Bearer {bearer}",
#     "Content-Type": "application/json",
# }
# print("headers: ", headers)
# response = requests.get(url, headers=headers)
# print("response: ", response)
# if response.status_code == 200:
#     instruments = response.json()
#     print("instruments: ", instruments)
#     for instrument in instruments:
#         if instrument["sn"] == instrumentSN:
#             return instrument
# if response.status_code == 401:
#     raise HTTPException(status_code=401, detail="Unauthorized - Please, update your bearer")
# if response.status_code == 403:
#     raise HTTPException(status_code=401, detail="Unauthorized")


def getInstrumentFromSN(db, instrumentSN):
    from modern.instrument import get_instruments

    instruments = get_instruments()
    for instrument in instruments:
        if instrument.sn == instrumentSN:
            return instrument.model_dump()
    return None


def getDriveId(db: DB, driveName) -> str:
    # url = f"{db}drives"
    # print("url: ", url)

    # headers = {
    #     "Authorization": f"Bearer {bearer}",
    #     "Content-Type": "application/json",
    # }
    # print("headers: ", headers)
    # response = requests.get(url, headers=headers)
    # print("response: ", response)
    # if response.status_code == 200:
    #     drives = response
    #     print("drives: ", drives)
    #     for drive in drives:
    #         if drive["name"] == driveName:
    #             return drive["id"]
    #         return drive["id"]
    #     return None
    # if response.status_code == 401:
    #     raise HTTPException(status_code=401, detail="Unauthorized - Please, update your bearer")
    # if response.status_code == 403:
    #     raise HTTPException(status_code=401, detail="Unauthorized")
    # return None

    drives = db.get("drives")
    print("response: ", drives)
    for drive in drives:
        if drive["name"] == driveName:
            return drive["id"]
    return None


# not use at this moment
# need for scanning
# def    postSample(projectId,sample,bearer,db):
#     # url = f"{dbserver.getUrl()}/projects"
#     url = f"{db}/projects/{projectId}/samples"
#     print("url: ", url)


#     headers = {
#         "Authorization": f"Bearer {bearer}",
#         "Content-Type": "application/json"
#     }

#     response = requests.post(url, json=sample, headers=headers)

#     if response.status_code != 200:
#         print("response: ", response)
#         print("response text: ", response.text)
#         raise HTTPException(status_code=response.status_code, detail="Error importing sample: " + response.text)

#     print("response: ", response)
#     print("response: ", response.status_code)

#     sampleid = response.json().get("id")
#     return sampleid
