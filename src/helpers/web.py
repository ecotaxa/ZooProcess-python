import sys
import traceback
from os import fstat
from pathlib import Path
from typing import Tuple, BinaryIO, Any

from fastapi import HTTPException
from starlette import status
from starlette.responses import PlainTextResponse

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


class AutoCloseBinaryIO(object):
    """
    An IO object which closes underlying file pointer when going out of scope.
    """

    def __init__(self, path: str):
        self.fd: BinaryIO = open(path, "rb")

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
            self.fd = None
            raise StopIteration()

    def __del__(self):
        if hasattr(self, "fd") and self.fd is not None:
            self.fd.close()
            self.fd = None


def get_stream(
    file_path: Path,
) -> Tuple[AutoCloseBinaryIO, int, str]:
    fp = AutoCloseBinaryIO(file_path.resolve().as_posix())
    media_type = "text/plain"
    file_name_lower = file_path.name.lower()
    if file_name_lower.endswith(".jpg"):
        media_type = "image/jpeg"
    elif file_name_lower.endswith(".png"):
        media_type = "image/png"
    elif file_name_lower.endswith(".tif"):
        media_type = "image/tiff"
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
        if a_line.find("main.py") != -1:
            our_stack_ndx = ndx
            break
    data = "\n----------- BACK-END -------------\n" + "".join(tb[our_stack_ndx:])
    return PlainTextResponse(data, status_code=status_code)
