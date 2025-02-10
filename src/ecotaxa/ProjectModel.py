from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict

class ContactModel(BaseModel):
    name: str
    email: EmailStr
    organisation: Optional[str]
    address: Optional[str]
    phone: Optional[str]

class ProjectModel(BaseModel):
    projid: int
    title: str
    visible: bool
    status: str
    objcount: int
    pctvalidated: float
    pctclassified: float
    classifsettings: Optional[Dict]
    initclassiflist: Optional[List[str]]
    managers: List[str]
    annotators: List[str]
    viewers: List[str]
    description: Optional[str]
    license: Optional[str]
    contact: Optional[ContactModel]
    citation: Optional[str]
