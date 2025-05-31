from fastapi import APIRouter, Depends
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Models import BackgroundUrl, ScanPostRsp
from auth import get_current_user_from_credentials
from config_rdr import config
from local_DB.db_dependencies import get_db
from local_DB.models import User
from logger import logger
from providers.server import Server

# Create a router instance without a prefix
router = APIRouter(
    tags=["images"],
)

# Initialize the database server
dbserver = Server(config.dbserver)


@router.post("/scan/{scan_id}/url")
def post_scan_url(
    scan_id: str,
    background_url: BackgroundUrl,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> ScanPostRsp:
    logger.info(f"Received scan URL: {background_url} for scan {scan_id}")
    return ScanPostRsp(id=scan_id, image="toto")
