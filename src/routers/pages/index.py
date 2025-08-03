from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from helpers.auth import get_current_user_from_credentials
from local_DB.db_dependencies import get_db
from local_DB.models import User
from helpers.logger import logger
from routers.pages.common import templates

# Create a router instance
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def get_index_page(
    request: Request,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Serve the index page.

    Args:
        request (Request): The FastAPI request object
        _user (User): The authenticated user
        db (Session): The database session

    Returns:
        HTMLResponse: The rendered HTML template
    """
    logger.info("Serving index page")
    context: Dict[str, Any] = {"request": request, "user": _user}
    return templates.TemplateResponse("index.html", context)
