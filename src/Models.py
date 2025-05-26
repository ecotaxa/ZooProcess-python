# Models for communicating via FastAPI
from datetime import datetime
from typing import List, Union, Literal, Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    name: str
    email: str


class Drive(BaseModel):
    """Drive model as defined in the OpenAPI specification"""

    id: str
    name: str
    url: Union[str, None] = None


class Project(BaseModel):
    """
    Project path: the path to the project folder
    name: [optional] the name of the project else take the name of the project folder
    instrumentSerialNumber: the serial number of the instrument need to be in the DB else raise an exception
    ecotaxaProjectID: [optional] the id of the ecotaxa project
    drive: [optional] the drive name, if empty the parent project folder name will be used. The drive name will be searched in the DB if not found, an exception will raise
    samples: [optional] a list of samples inside the project
    instrument: [optional] the instrument used for this project
    createdAt: [optional] the creation date of the project
    updatedAt: [optional] the last update date of the project
    """

    bearer: str = ""  # Union[str, None] = None
    db: str = ""  # Union[str, None] = None
    path: str
    id: str
    name: Union[str, None] = None
    instrumentSerialNumber: str  # Union[str, None] = None
    instrumentId: Optional[str] = None  # A Project can be uninitialized
    acronym: Union[str, None] = None
    description: Union[str, None] = None
    ecotaxaProjectID: Union[str, None] = None
    drive: "Drive"
    samples: Union[List["Sample"], None] = None
    instrument: "Instrument"
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class Sample(BaseModel):
    """
    Sample model as defined in the OpenAPI specification.
    _This_ kind of sample is returned inside a Project.
    """

    id: str
    name: str
    subsample: Union[List["SubSample"], None] = None
    metadata: Union[List["MetadataModel"], None] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class SampleWithBackRef(Sample):
    """
    Sample model as defined in the OpenAPI specification.
    _This_ kind of sample is returned when queried uniquely.
    """

    projectId: str
    project: Project


class SubSample(BaseModel):
    """SubSample model as defined in the OpenAPI specification"""

    id: str
    name: Union[str, None] = None


class Folder(BaseModel):
    bearer: Optional[str] = None
    db: Optional[str] = None
    path: str
    taskId: Union[str, None] = None
    scanId: Union[str, None] = None


class Background(BaseModel):
    id: str
    name: str
    url: str
    user: User
    instrument: "Instrument"
    createdAt: datetime
    error: Optional[datetime] = None
    # path: str
    # bearer: str | None = None
    # bd: str | None = None
    # taskId: Union[str, None] = None
    # back1scanId: str
    # back2scanId: str
    # projectId: str
    # background: List[str]
    # instrumentId: str


class BMProcess(BaseModel):
    bearer: Union[str, None] = None
    db: Union[str, None] = None
    src: str
    dst: Union[str, None] = None
    scan: str
    back: str
    taskId: Union[str, None] = None


class ScanIn(BaseModel):
    """As POST-ed"""

    scanId: str
    bearer: str


class Scan(BaseModel):
    """As GET returns"""

    id: str
    url: str
    type: str
    archived: bool = False
    deleted: bool = False
    metadata: Optional[List["MetadataModel"]] = None
    user: User


class LoginReq(BaseModel):
    """Login request model as defined in the OpenAPI specification"""

    email: str = Field(
        ...,
        json_schema_extra={
            "description": "User email used during registration",
            "example": "ecotaxa.api.user@gmail.com",
        },
    )
    password: str = Field(
        ..., json_schema_extra={"description": "User password", "example": "test!"}
    )


class Calibration(BaseModel):
    """Calibration model as defined in the OpenAPI specification"""

    id: str
    frame: str
    xOffset: float
    yOffset: float
    xSize: float
    ySize: float


class Instrument(BaseModel):
    """Instrument model as defined in the OpenAPI specification"""

    id: str
    model: Literal["Zooscan"] = "Zooscan"
    name: str
    sn: str
    ZooscanCalibration: Optional[List[Calibration]] = None


class MetadataModel(BaseModel):
    """Metadata model as defined in the OpenAPI specification"""

    id: str
    name: str
    value: str
    description: Optional[str] = None
