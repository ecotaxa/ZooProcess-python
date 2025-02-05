
from pydantic import BaseModel
from typing import Union


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
