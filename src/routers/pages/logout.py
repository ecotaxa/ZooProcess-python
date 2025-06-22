from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from helpers.auth import get_current_user_from_credentials, SESSION_COOKIE_NAME
from local_DB.db_dependencies import get_db
from logger import logger
from routers.pages.common import templates

# Create a router instance
router = APIRouter()


@router.get("/logout", response_class=HTMLResponse)
async def ui_logout(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_from_credentials),
) -> HTMLResponse:
    """
    UI Logout endpoint that invalidates the current JWT token and renders a logout confirmation page.

    Args:
        request (Request): The FastAPI request object
        db (Session): The database session
        user: The authenticated user

    Returns:
        HTMLResponse: The rendered logout confirmation page
    """
    logger.info("User logging out via UI")

    # Render the logout confirmation page
    context: Dict[str, Any] = {"request": request}
    template_response = templates.TemplateResponse("logout.html", context)

    # Set an invalid session cookie to effectively log the user out
    template_response.set_cookie(
        key=SESSION_COOKIE_NAME, value="invalid", httponly=True
    )

    return template_response
