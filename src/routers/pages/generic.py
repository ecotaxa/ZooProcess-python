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


@router.get("/{page_name}", response_class=HTMLResponse)
def get_page(
    page_name: str,
    request: Request,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Serve a specific page by name.

    Args:
        page_name (str): The name of the page to serve
        request (Request): The FastAPI request object
        _user (User): The authenticated user
        db (Session): The database session

    Returns:
        HTMLResponse: The rendered HTML template
    """
    logger.info(f"Serving page: {page_name}")
    context: Dict[str, Any] = {
        "request": request,
        "user": _user,
        "page_name": page_name,
    }
    return templates.TemplateResponse(f"{page_name}.html", context)
