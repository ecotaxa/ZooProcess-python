from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from helpers.auth import (
    SESSION_COOKIE_NAME,
    authenticate_user,
)
from local_DB.db_dependencies import get_db
from helpers.logger import logger
from routers.pages.common import templates

# Create a router instance
router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def get_login_page(
    request: Request,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Serve the login page.

    Args:
        request (Request): The FastAPI request object
        error (Optional[str]): Optional error message to display
        db (Session): The database session

    Returns:
        HTMLResponse: The rendered HTML template
    """
    logger.info("Serving login page")
    context: Dict[str, Any] = {"request": request, "error": error}
    return templates.TemplateResponse("login.html", context)


@router.post("/login")
async def ui_login_post(request: Request, db: Session = Depends(get_db)):
    """
    UI Login endpoint for form submissions

    If successful, sets a session cookie with the JWT token and redirects to the home page.
    If unsuccessful, returns to the login page with an error message.
    """
    # Get form data
    form_data = await request.form()
    email = str(form_data.get("email"))
    password = str(form_data.get("password"))

    try:
        # Authenticate user and get token
        token = authenticate_user(email, password, db)

        # Create a redirect response to the home page
        response = RedirectResponse(url="/ui/", status_code=303)

        # Set the token in a session cookie
        response.set_cookie(key=SESSION_COOKIE_NAME, value=token, httponly=True)

        return response
    except HTTPException as e:
        # If authentication fails, return to the login page with an error message
        return get_login_page(request, error=e.detail, db=db)
