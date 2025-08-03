# Main
import shutil
import typing
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import Response

from Models import (
    ScanIn,
    Background,
    User,
    LoginReq,
    Drive,
    ImageUrl,
    ForInstrumentBackgroundIn,
)
from helpers.auth import SESSION_COOKIE_NAME, authenticate_user, blacklist_token
from helpers.auth import get_current_user_from_credentials
from helpers.web import (
    internal_server_error_handler,
    TimingMiddleware,
    validation_exception_handler,
    unauthorized_exception_handler,
    raise_500,
    raise_501,
)
from img_proc.convert import convert_tiff_to_jpeg
from legacy import LegacyTimeStamp
from legacy.backgrounds import LegacyBackgroundDir
from legacy.drives import validate_drives
from legacy.writers.background import file_name_for_raw_background
from local_DB.db_dependencies import get_db
from local_DB.models import init_db
from helpers.logger import logger
from modern.app_urls import is_download_url, extract_file_id_from_download_url
from modern.files import UPLOAD_DIR
from modern.from_legacy import (
    drives_from_legacy,
    backgrounds_from_legacy_project,
)
from modern.tasks import JobScheduler
from routers.images import router as images_router
from routers.instruments import (
    router as instruments_router,
)
from routers.pages import router as pages_router
from routers.projects import router as projects_router
from routers.samples import router as samples_router
from routers.subsamples import router as subsamples_router
from routers.tasks import router as tasks_router
from routers.utils import validate_path_components
from routers.vignettes import router as vignettes_router
from static.favicon import create_plankton_favicon

JOB_INTERVAL = 2


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan event handler for application startup and shutdown"""
    # Run validation on application startup
    validate_drives()

    # Initialize database tables if they don't exist
    logger.info("Initializing database tables")
    init_db()
    JobScheduler.launch_at_interval(JOB_INTERVAL)

    yield
    # Cleanup code
    JobScheduler.shutdown()


# Initialize FastAPI with lifespan event handler
app = FastAPI(lifespan=lifespan)

# Add exception handlers for 500, 422 (validation), and 401 (unauthorized) errors
app.add_exception_handler(
    status.HTTP_500_INTERNAL_SERVER_ERROR, internal_server_error_handler
)
app.add_exception_handler(
    RequestValidationError, validation_exception_handler  # type:ignore
)
app.add_exception_handler(
    status.HTTP_401_UNAUTHORIZED, unauthorized_exception_handler  # type:ignore
)
# https://github.com/encode/starlette/pull/2403

origins = [
    "*",
    "localhost",
    "zooprocess.imev-mer.fr",
    "localhost:8000",
    "imev:3001",
    # "http://localhost",
    # "http://localhost:8000",
    # "http://localhost:3001",
    # "http://127.0.0.1:59245",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add timing middleware to log execution time of all endpoints
app.add_middleware(TimingMiddleware)

# Mount the static directory to serve static files
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)

# Include the routers
app.include_router(projects_router)
app.include_router(samples_router)
app.include_router(subsamples_router)
app.include_router(instruments_router)
app.include_router(images_router)
app.include_router(tasks_router)
app.include_router(vignettes_router)
app.include_router(pages_router)


@app.get("/favicon.ico")
def get_favicon():
    """
    Serve a plankton-inspired favicon.

    Returns:
        Response: A response containing the favicon image.
    """
    favicon_bytes = create_plankton_favicon()
    return Response(content=favicon_bytes.getvalue(), media_type="image/x-icon")


@app.post("/separator/scan")
def separate_scan(scan: ScanIn) -> None:
    # import os

    logger.info(f"POST /separator/scan: {scan}")

    # Separate(scan.scanId, scan.bearer, separateServer)
    raise_500("Not Implemented")


@app.post("/convert/")
def convert(image: ImageUrl):
    """Convert an image from tiff to jpeg format"""
    logger.info(f"Request to convert {image.src} to {image.dst}")

    if is_download_url(image.src):
        src_image_path = UPLOAD_DIR / extract_file_id_from_download_url(image.src)
    else:
        src_image_path = Path(image.src)
    dst_image_path = Path(image.dst)

    try:
        file_out = convert_tiff_to_jpeg(src_image_path, dst_image_path)
        return file_out
    except Exception as e:
        logger.exception(e)
        raise_500(f"Cannot convert {image.src}")
        return None


@app.post("/background/{instrument_id}/url")
@typing.no_type_check
def add_background_for_instrument(
    instrument_id: str,
    projectId: str,
    background: ForInstrumentBackgroundIn,
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> Background:
    logger.info(
        f"add_background_for_instrument instrument_id: {instrument_id}, projectId: {projectId}, background: {background}"
    )
    _, zoo_project, _, _ = validate_path_components(db, background.projectId)
    if not is_download_url(background.url):
        raise_501("Invalid background URL, not produced here")
    src_image_path = UPLOAD_DIR / extract_file_id_from_download_url(background.url)
    # AFAICS, there is no indication that the bg is the first or the second one in the API
    # but the 2 backgrounds have to end up with the same timestamp
    stamp = LegacyTimeStamp()
    two_mins_ago = stamp.subtract_minutes(2)
    lgcy_dir = LegacyBackgroundDir(zoo_project)
    recent_additions_dates = lgcy_dir.dates_younger_than(two_mins_ago)
    if len(recent_additions_dates) > 0:
        stamp = recent_additions_dates[0]
        logger.info(
            f"Recent background date: {recent_additions_dates}, last: {stamp}, entries: {lgcy_dir.entries_by_date[stamp.to_string()]}"
        )
        frame_num = 2
    else:
        frame_num = 1
    dst_file_name = file_name_for_raw_background(stamp.to_string(), frame_num)
    dst_file_path = zoo_project.zooscan_back.path / dst_file_name
    logger.info(f"Copying to dst_file_name: {dst_file_path}")
    shutil.copyfile(src_image_path, dst_file_path)
    zoo_project.zooscan_back.read()  # Refresh content
    for_all = backgrounds_from_legacy_project(zoo_project, stamp.to_string())
    return for_all[0]


@app.post("/login")
def login_post(login_req: LoginReq, db: Session = Depends(get_db)):
    """
    Login endpoint

    If successful, returns a JWT token which will have to be used in bearer authentication scheme for subsequent calls.
    """
    # Authenticate user and get token
    token = authenticate_user(login_req.email, login_req.password, db)

    # Return the token as a JSON response
    return JSONResponse(content=token)


@app.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_from_credentials),
):
    """
    Logout endpoint that invalidates the current JWT token.

    This endpoint requires authentication using a JWT token obtained from the /login endpoint.
    It adds the token to a blacklist (burnt list) to prevent its further use and returns an invalid session cookie.
    """
    token = None

    # Try to extract token from the authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")

    # If no token from header, try to get it from the session cookie
    if not token:
        token = request.cookies.get(SESSION_COOKIE_NAME)

    # If we have a token, blacklist it
    if token:
        blacklist_token(token, db)

    # Set an invalid session cookie instead of deleting it
    response.set_cookie(key=SESSION_COOKIE_NAME, value="invalid", httponly=True)

    return {"message": "Successfully logged out"}


@app.get("/users/me")
def get_current_user(
    user=Depends(get_current_user_from_credentials),
):
    """
    Returns information about the currently authenticated user.

    This endpoint requires authentication using a JWT token obtained from the /login endpoint.
    """
    # Return the user information
    return User(id=user.id, name=user.name, email=user.email)


@app.get("/drives")
def get_drives(
    user=Depends(get_current_user_from_credentials),
) -> List[Drive]:
    """
    Returns a list of all drives.
    This endpoint requires authentication using a JWT token obtained from the /login endpoint.
    """
    return drives_from_legacy()


@app.get("/ping")
def ping():
    """
    Simple health check endpoint that returns 'pong!'.

    This endpoint can be used to verify that the server is running and responding to requests.
    """
    logger.info("Ping endpoint called")
    return "pong!"


@app.get("/crash")
def crash_endpoint():
    """
    Endpoint that deliberately raises an exception to test error handling and logging.

    This endpoint will always return a 500 Internal Server Error and log the stack trace.
    """
    logger.info("Crash endpoint called - about to raise an exception")
    # Deliberately raise an exception
    raise Exception("This is a deliberate crash for testing error handling")


# Start the application when run directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
