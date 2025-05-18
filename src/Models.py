from typing import List, Union

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    name: str
    email: str


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
