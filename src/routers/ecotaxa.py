from typing import List, Dict, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Models import Project
from config_rdr import config
from helpers.auth import get_current_user_from_credentials, create_jwt_token
from helpers.logger import logger
from local_DB.db_dependencies import get_db
from providers.EcoTaxa.ecotaxa_model import ProjectModel, LoginReq
from providers.ecotaxa_client import EcoTaxaApiClient

# Create a routers instance
router = APIRouter(
    prefix="/ecotaxa",
    tags=["ecotaxa"],
)


@router.get("/projects", response_model=List[ProjectModel])
def get_projects(
    token: str,
    _user=Depends(get_current_user_from_credentials),
    _db: Session = Depends(get_db),
) -> List[Project]:
    """
    Get a list of ZooScan projects from EcoTaxa.

    Args:
        _user: The authenticated user
        _db: The database session

    Returns:
        List[Project]: A list of ZooScan projects
    """
    client = EcoTaxaApiClient.from_token(logger, config.ECOTAXA_SERVER, token)
    return client.list_zooscan_projects()


@router.post("/login")
def ecotaxa_login(
    login_req: LoginReq,
    _user=Depends(get_current_user_from_credentials),
    _db: Session = Depends(get_db),
):
    """
    Authenticates with EcoTaxa using the provided credentials.

    Args:
        login_req (LoginReq): The login request containing username (email) and password.
        _user: The authenticated user
        _db: The database session

    Returns:
        Dict: A dictionary containing the JWT-encrypted EcoTaxa token.
    """
    client = EcoTaxaApiClient(
        logger, config.ECOTAXA_SERVER, login_req.username, login_req.password
    )
    ecotaxa_token: Optional[str] = None
    try:
        ecotaxa_token = client.login()
    except Exception as err:
        pass
    if ecotaxa_token is None:
        return {"token": None}

    # Create a data dictionary for the JWT token
    token_data = {
        "ecotaxa_token": ecotaxa_token,
    }
    # Create a JWT token with 30-day expiration (similar to user sessions)
    jwt_token = create_jwt_token(token_data, expires_delta=30 * 24 * 60 * 60)

    return {"token": jwt_token}
