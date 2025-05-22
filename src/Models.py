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
    bearer: the bearer token to use for the request
    db: the database to use for the request
    name: [optional] the name of the project else take the name of the project folder
    instrumentSerialNumber: the serial number of the instrument need to be in the DB else raise an exception
    ecotaxaProjectID: [optional] the id of the ecotaxa project
    drive: [optional] the drive name, if empty the parent project folder name will be used. The drive name will be searched in the DB if not found, an exception will raise
    samples: [optional] a list of samples inside the project
    """

    path: str
    id: str
    bearer: str = ""  # Union[str, None] = None
    db: str = ""  # Union[str, None] = None
    name: Union[str, None] = None
    instrumentSerialNumber: str  # Union[str, None] = None
    acronym: Union[str, None] = None
    description: Union[str, None] = None
    ecotaxaProjectID: Union[str, None] = None
    drive: Union["Drive", None] = None
    samples: Union[List["Sample"], None] = None


class Sample(BaseModel):
    """Sample model as defined in the OpenAPI specification"""

    id: str
    name: str
    subsample: Union[List["SubSample"], None] = None
    metadata: Union[List["MetadataModel"], None] = None


class SubSample(BaseModel):
    """SubSample model as defined in the OpenAPI specification"""

    id: str
    name: Union[str, None] = None


class Folder(BaseModel):
    path: str
    # bearer: str | None = None
    # bd: str | None = None
    bearer: Union[str, None] = None
    db: Union[str, None] = None
    taskId: Union[str, None] = None
    scanId: Union[str, None] = None


class Background(BaseModel):
    # path: str
    # bearer: str | None = None
    # bd: str | None = None
    bearer: Union[str, None] = None
    db: Union[str, None] = None
    taskId: Union[str, None] = None
    # back1scanId: str
    # back2scanId: str
    projectId: str
    background: List[str]
    instrumentId: str


class BMProcess(BaseModel):
    src: str
    dst: Union[str, None] = None
    scan: str
    back: str
    taskId: Union[str, None] = None
    bearer: Union[str, None] = None
    db: Union[str, None] = None


class Scan(BaseModel):
    scanId: str
    bearer: str


class LoginReq(BaseModel):
    """Login request model as defined in the OpenAPI specification"""

    email: str = Field(
        ...,
        description="User email used during registration",
        example="ecotaxa.api.user@gmail.com",
    )
    password: str = Field(..., description="User password", example="test!")


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
    model: Literal["Zooscan"]
    name: str
    sn: str
    ZooscanCalibration: Optional[List[Calibration]] = None


class MetadataModel(BaseModel):
    """Metadata model as defined in the OpenAPI specification"""

    id: str
    name: str
    value: str
    description: Optional[str] = None
