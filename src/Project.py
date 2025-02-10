
from pydantic import BaseModel
from typing import Union


class Project(BaseModel):
    """
        Project path: the path to the project folder
        bearer: the bearer token to use for the request
        db: the database to use for the request
        name: [optional] the name of the project else take the name of the project folder
        instrumentSerialNumber: the serial number of the instrument else instrument will marked undefine in the DB
        ecotaxaProjectID: [optional] the id of the ecotaxa project
    """
    path: str 
    bearer: str #Union[str, None] = None
    db: str #Union[str, None] = None
    name: Union[str, None] = None
    instrumentSerialNumber: str #Union[str, None] = None 
    acronym: Union[str, None] = None 
    description: Union[str, None] = None
    ecotaxaProjectID: Union[str, None] = None
