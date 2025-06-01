from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Models import ScanToUrlReq, ScanPostRsp
from auth import get_current_user_from_credentials
from local_DB.db_dependencies import get_db
from local_DB.models import User
from logger import logger

# Create a router instance without a prefix
router = APIRouter(
    tags=["images"],
)


@router.post("/scan/{scan_id}/url")
def post_scan_url(
    scan_id: str,
    scan_url: ScanToUrlReq,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> ScanPostRsp:
    logger.info(f"Received scan URL: {scan_url} for scan {scan_id}")
    return ScanPostRsp(id=scan_id + "XXXX", image="toto")
