# Models for communicating via FastAPI
from datetime import datetime
from enum import Enum
from typing import List, Union, Literal, Optional, Dict, Any

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
    _This_ kind of sample is returned as child of a Project.
    """

    id: str
    name: str
    subsample: List["SubSample"]
    metadata: List["MetadataModel"]
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    nbScans: int
    nbFractions: str
    metadataModel: str = "foo"  # WIP on front side, but needed for form display


class SampleWithBackRef(Sample):
    """
    Sample model as defined in the OpenAPI specification.
    _This_ kind of sample is returned when queried uniquely.
    """

    projectId: str
    project: Project


class SubSample(BaseModel):
    """SubSample model as defined in the OpenAPI specification"""

    id: str  # The technical id
    name: str
    metadata: List["MetadataModel"]
    scan: List["Scan"]
    createdAt: datetime
    updatedAt: datetime
    user: User


class SubSampleIn(BaseModel):
    """A POST-ed subsample"""

    name: str
    metadataModelId: str  # TODO: Hardcoded on UI side
    # TODO: enforce fields AKA keys in below data, e.g.
    #  'scanning_operator': 'Admin',
    #  'scan_id': 'd1_01',
    #  'fraction_number': 'd1',
    #  'fraction_id_suffix': '01',
    #  'fraction_min_mesh': 200,
    #  'fraction_max_mesh': 300,
    #  'spliting_ratio': 4,
    #  'observation': 'sss'
    data: dict


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
    type: str
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


class LinkBackgroundReq(BaseModel):
    scanId: str


class ScanToUrlReq(BaseModel):
    instrumentId: str  # e.g. sn003
    projectId: str
    subsampleId: str
    url: str


class ScanTypeNum(str, Enum):
    SCAN = "SCAN"
    BACKGROUND = "BACKGROUND"
    MASK = "MASK"
    RAW_BACKGROUND = "RAW_BACKGROUND"
    VIS = "VIS"
    MEDIUM_BACKGROUND = "MEDIUM_BACKGROUND"
    CHECK_BACKGROUND = "CHECK_BACKGROUND"
    OUT = "OUT"


class ScanPostRsp(BaseModel):
    id: str
    image: str


class UploadPostRsp(BaseModel):
    fileUrl: str


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
    type: ScanTypeNum
    archived: bool = False
    deleted: bool = False
    metadata: List["MetadataModel"]
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

    name: str
    value: str
    type: str


class MetadataTemplateModel(BaseModel):
    """Metadata template model, basically some info on each metadata field"""

    id: str
    name: str
    description: str


class ImageUrl(BaseModel):
    src: str
    dst: Union[str, None] = None


class VignetteFolder(BaseModel):
    src: str
    base: str
    output: str


class TaskIn(BaseModel):
    exec: str
    params: Dict[str, Any]


class Task(TaskIn):
    id: str
    log: Optional[str]  # url to log file
    percent: int
    status: Literal["PENDING", "RUNNING", "FINISHED", "FAILED"]
    createdAt: datetime
    updatedAt: datetime
