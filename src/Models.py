# Models for communicating via FastAPI
from datetime import datetime
from enum import Enum
from typing import List, Union, Literal, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class User(BaseModel):
    id: str
    name: str
    email: str


class Drive(BaseModel):
    """Drive model as defined in the OpenAPI specification"""

    id: str
    name: str
    url: str


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


class SubSampleData(BaseModel):
    """Data model for subsample information"""

    scanning_operator: str
    scan_id: str
    fraction_id: str  # tot, d1, d2, ...
    fraction_id_suffix: str  # 1_sur_3
    fraction_min_mesh: int
    fraction_max_mesh: int
    spliting_ratio: int
    observation: str
    submethod: str

    @field_validator(
        "scanning_operator",
        "scan_id",
        "fraction_id",
        # "fraction_id_suffix", # It's OK to have no suffix, e.g. with 'tot'
        "observation",
        "submethod",
    )
    def validate_non_empty_string(cls, v):
        """Validate that string fields are not empty"""
        if not v or not v.strip():
            raise ValueError("String fields cannot be empty")
        return v

    @field_validator("fraction_max_mesh")
    def validate_fraction_max_mesh(cls, v, info):
        """Validate that fraction_max_mesh is larger than fraction_min_mesh"""
        values = info.data
        if "fraction_min_mesh" in values and v <= values["fraction_min_mesh"]:
            raise ValueError("fraction_max_mesh must be larger than fraction_min_mesh")
        return v


class SubSampleIn(BaseModel):
    """A POST-ed subsample"""

    name: str
    metadataModelId: str  # TODO: Hardcoded on UI side
    data: SubSampleData


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
    type: "ScanTypeEnum"
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


class ForInstrumentBackgroundIn(BaseModel):
    url: str
    projectId: str
    type: Optional[str]


class LinkBackgroundReq(BaseModel):
    scanId: str


class ScanToUrlReq(BaseModel):
    instrumentId: str  # e.g. sn003
    url: str


class ScanTypeEnum(str, Enum):
    RAW_BACKGROUND = "RAW_BACKGROUND"  # From scanner, up to 2 of them with names "back_large_raw_1.tif" and "back_large_raw_2.tif"
    BACKGROUND = (
        "BACKGROUND"  # 8-bit version of the raw backgrounds, same name without "_raw"
    )
    MEDIUM_BACKGROUND = "MEDIUM_BACKGROUND"  # Addition of the 2
    SCAN = "SCAN"
    MASK = "MASK"
    VIS = "VIS"
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


class ScanSubsample(BaseModel):
    """Link b/w scan and subsample. TODO: Clean on front side"""

    subsample: SubSample  # A scan belongs to a subsample


class Scan(BaseModel):
    """As GET returns"""

    id: str
    url: str
    type: ScanTypeEnum
    archived: bool = False
    deleted: bool = False
    metadata: List["MetadataModel"]
    scanSubsamples: List[ScanSubsample]
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
    dst: str


class VignetteFolder(BaseModel):
    src: str
    base: str
    output: str


class TaskReq(BaseModel):
    exec: str
    params: Dict[str, Any]


class TaskRsp(TaskReq):
    id: str
    log: Optional[str]  # url to log file
    percent: int
    status: Literal["PENDING", "RUNNING", "FINISHED", "FAILED"]
    createdAt: datetime
    updatedAt: datetime
