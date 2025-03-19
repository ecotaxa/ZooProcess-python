
from pydantic import BaseModel
from typing import Union


class Project(BaseModel):
    """
        Project path: the path to the project folder
        bearer: the bearer token to use for the request
        db: the database to use for the request
        name: [optional] the name of the project else take the name of the project folder
        instrumentSerialNumber: the serial number of the instrument need to be in the DB else raise an exception
        ecotaxaProjectID: [optional] the id of the ecotaxa project
        drive: [optional] the drive name, if empty the parent project folder name will be used. The drive name will be searched in the DB if not found, an exception will raise
    """
    path: str 
    bearer: str #Union[str, None] = None
    db: str #Union[str, None] = None
    name: Union[str, None] = None
    instrumentSerialNumber: str #Union[str, None] = None 
    acronym: Union[str, None] = None 
    description: Union[str, None] = None
    ecotaxaProjectID: Union[str, None] = None
    drive: Union[str, None] = None
