from logger import logger
from remote.DB import DB


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
