from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from Models import ScanPostRsp, UploadPostRsp
from helpers.web import get_stream
from local_DB.db_dependencies import get_db
from local_DB.models import User
from helpers.logger import logger
from modern.app_urls import get_download_url
from modern.files import add_file, UPLOAD_DIR

# Create a router instance without a prefix
router = APIRouter(
    tags=["images"],
)


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
        f"Receiving file upload: {file.filename}, content_type: {file.content_type}"
    )

    # Generate an ID for the uploaded file
    file_id = f"upload_{file.filename}"
    await add_file(file_id, file)

    logger.info(
        f"Received file upload: {file.filename}, content_type: {file.content_type}"
    )

    file_url = get_download_url(file_id)
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
