import os
import sys
import tempfile
import time
import traceback
from os import fstat
from pathlib import Path
from typing import Tuple, BinaryIO, Any, Coroutine

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, JSONResponse, RedirectResponse

from logger import logger


def raise_500(error_message: str):
    """
    Logs an error and raises an HTTP 500 exception.

    Args:
        error_message (str): The error message to log and include in the exception detail.

    Raises:
        HTTPException: An HTTP 500 exception with the provided error message as detail.
    """
    logger.error(error_message)
    raise HTTPException(status_code=500, detail=error_message)


def raise_404(error_message: str):
    """
    Logs an error and raises an HTTP 404 exception.

    Args:
        error_message (str): The error message to log and include in the exception detail.

    Raises:
        HTTPException: An HTTP 404 exception with the provided error message as detail.
    """
    logger.info(error_message)
    raise HTTPException(status_code=404, detail=error_message)


def raise_422(error_message: str):
    """
    Logs an error and raises an HTTP 422 exception (validation error).

    Args:
        error_message (str): The error message to log and include in the exception detail.

    Raises:
        HTTPException: An HTTP 404 exception with the provided error message as detail.
    """
    logger.info(error_message)
    raise HTTPException(status_code=422, detail=error_message)


def raise_501(error_message: str):
    """
    Logs an error and raises an HTTP 501 exception for not implemented functionality.

    Args:
        error_message (str): The error message to log and include in the exception detail.

    Raises:
        HTTPException: An HTTP 501 exception with the provided error message as detail.
    """
    logger.info(error_message)
    raise HTTPException(status_code=501, detail=error_message)


TEMP_PATH_PRFX = tempfile.gettempdir() + os.sep + tempfile.gettempprefix()


class AutoCloseBinaryIO(object):
    """
    An IO object which closes the underlying file pointer when going out of scope.
    If the file is a temp one, also delete it when done with streaming.
    """

    def __init__(self, path: str):
        self.fd: BinaryIO = open(path, "rb")
        self.to_unlink = path if path.startswith(TEMP_PATH_PRFX) else None

    def size(self) -> int:
        return fstat(self.fd.fileno()).st_size

    def seek(self, offset: int):
        return self.fd.seek(offset)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return self.fd.__next__()
        except StopIteration:
            self.fd.close()
            self.fd = None  # type:ignore
            if self.to_unlink is not None:
                os.unlink(self.to_unlink)
            raise StopIteration()

    def __del__(self):
        if hasattr(self, "fd") and self.fd is not None:
            self.fd.close()
            self.fd = None  # type:ignore


def get_stream(
    file_path: Path,
) -> Tuple[AutoCloseBinaryIO, int, str]:
    fp = AutoCloseBinaryIO(file_path.resolve().as_posix())
    media_type = "text/plain"
    file_name_lower = file_path.name.lower()
    match file_name_lower:
        case name if name.endswith(".jpg"):
            media_type = "image/jpeg"
        case name if name.endswith(".png"):
            media_type = "image/png"
        case name if name.endswith(".tif"):
            media_type = "image/tiff"
        case name if name.endswith(".gif"):
            media_type = "image/gif"
        case name if name.endswith(".gz"):
            media_type = "application/gzip"
        case _:
            pass
    return fp, fp.size(), media_type


async def internal_server_error_handler(
    _request: Any, exc: Exception
) -> PlainTextResponse:
    """
        Override internal error handler, so that we don't have to look at logs on server side in case of problem.
    :param _request:
    :param exc: The exception caught.
    :return:
    """
    tpe, val, tbk = sys.exc_info()
    status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
    tb = traceback.format_exception(tpe, val, tbk)
    our_stack_ndx = 0
    # Remove all until our code
    for ndx, a_line in enumerate(tb):
        if a_line.find("src/main.py") != -1 or (a_line.find("src/routers") != -1):
            our_stack_ndx = ndx
    our_tb = "".join(tb[our_stack_ndx:])
    data = "\n----------- BACK-END -------------\n" + our_tb
    logger.error(our_tb)
    return PlainTextResponse(data, status_code=status_code)


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Request to {request.url.path} took {process_time:.4f} seconds")
        return response


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Get the request body
    body = await request.body()

    # Log the validation error with the request body
    logger.error(f"Validation error: {exc.errors()}, Request body: {body.decode()}")

    # Return the standard validation error response
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc.errors())},
    )


async def unauthorized_exception_handler(
    request: Request, exc: HTTPException
) -> RedirectResponse | JSONResponse:
    """
    Handle 401 Unauthorized errors for UI endpoints by redirecting to the login page.
    For API endpoints, return the standard 401 response.

    Args:
        request (Request): The request that caused the exception
        exc (HTTPException): The exception that was raised

    Returns:
        JSONResponse: Either a redirect response or the standard 401 response
    """
    # Check if this is a UI endpoint (starts with /ui)
    if request.url.path.startswith("/ui"):
        logger.info(
            f"Redirecting unauthorized UI request to login page: {request.url.path}"
        )
        # Create a redirect response to the login page
        from starlette.responses import RedirectResponse

        return RedirectResponse(url="/ui/login", status_code=302)

    # For non-UI endpoints, return the standard 401 response
    logger.info(f"Unauthorized API request: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail},
        headers=exc.headers,
    )
