from typing import List

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from Models import Project
from config_rdr import config
from helpers.auth import (
    get_current_user_from_credentials,
    get_ecotaxa_token_from_credentials,
)
from helpers.logger import logger
from local_DB.db_dependencies import get_db
from providers.EcoTaxa.ecotaxa_model import ProjectModel
from providers.ecotaxa_client import EcoTaxaApiClient

# Create a routers instance
router = APIRouter(
    prefix="/ecotaxa",
    tags=["ecotaxa"],
)


@router.get("/projects", response_model=List[ProjectModel])
def get_projects(
    _user=Depends(get_current_user_from_credentials),
    ecotaxa_token: HTTPAuthorizationCredentials = Depends(
        get_ecotaxa_token_from_credentials
    ),
    db: Session = Depends(get_db),
) -> List[ProjectModel]:
    """
    Get a list of ZooScan projects from EcoTaxa.

    Args:
        _user: The authenticated user
        ecotaxa_token: embedded EcoTaxa token
        db: The database session

    Returns:
        List[Project]: A list of ZooScan projects
    """
    assert isinstance(ecotaxa_token, str), "Failed to decode JWT-encoded EcoTaxa token"

    client = EcoTaxaApiClient.from_token(logger, config.ECOTAXA_SERVER, ecotaxa_token)
    return client.list_zooscan_projects()
