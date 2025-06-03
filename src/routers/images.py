from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from Models import ScanToUrlReq, ScanPostRsp, UploadPostRsp
from auth import get_current_user_from_credentials
from config_rdr import config
from helpers.web import get_stream
from local_DB.db_dependencies import get_db
from local_DB.models import User
from logger import logger
from modern.files import add_file, UPLOAD_DIR

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


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    # _user: User = Depends(get_current_user_from_credentials), # TODO on front side
    db: Session = Depends(get_db),
) -> UploadPostRsp:
    """
    Upload an image file using form-encoded data.

    Args:
        file (UploadFile): The image file to upload.
        _user (User): The authenticated user.
        db (Session): Database session.

    Returns:
        ScanPostRsp: Response containing the ID and image information.
    """
    logger.info(
        f"Received file upload: {file.filename}, content_type: {file.content_type}"
    )

    # Generate an ID for the uploaded file
    file_id = f"upload_{file.filename}"
    await add_file(file_id, file)

    file_url = config.public_url + "/download/" + file_id
    return UploadPostRsp(fileUrl=file_url)


@router.get("/download/{image_ref}")
async def get_uploaded_image(
    image_ref: str,
    # _user=Depends(get_current_user_from_credentials),
) -> StreamingResponse:
    """
    Get an uploaded image for visualization.
    """
    tmp_file = UPLOAD_DIR / image_ref
    # Stream the file
    file_like, length, media_type = get_stream(tmp_file)
    headers = {"content-length": str(length)}
    return StreamingResponse(file_like, headers=headers, media_type=media_type)
