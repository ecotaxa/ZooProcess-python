from fastapi import HTTPException
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
    logger.error(error_message)
    raise HTTPException(status_code=404, detail=error_message)
