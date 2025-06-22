from pathlib import Path
from typing import Any, Dict, Optional, NamedTuple, List

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from helpers.auth import (
    get_current_user_from_credentials,
    SESSION_COOKIE_NAME,
    authenticate_user,
)
from local_DB.db_dependencies import get_db
from local_DB.models import User
from logger import logger
from routers.projects import get_projects as api_get_projects


class ProjectItem(NamedTuple):
    """
    A flattened representation of project data including scan, subsample, sample, and project information.
    """

    scan: Any  # Scan object or count
    subsample: Any  # SubSample object
    sample: Any  # Sample object
    project: Any  # Project object


# Define the templates directory
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Create a router instance with prefix "/pages"
router = APIRouter(
    prefix="/ui",
    tags=["pages"],
)


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


@router.get("/projects", response_class=HTMLResponse)
def get_projects_page(
    request: Request,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Serve the projects page with a list of ProjectItem NamedTuples containing scan, subsample, sample, and project information.
    Samples without subsamples are discarded.

    Args:
        request (Request): The FastAPI request object
        _user (User): The authenticated user
        db (Session): The database session

    Returns:
        HTMLResponse: The rendered HTML template
    """
    logger.info("Serving projects page")
    # Get projects data using the API
    projects = api_get_projects(_user=_user, db=db)

    # Transform the tree structure into a list of ProjectItem objects
    project_items: List[ProjectItem] = []

    for project in projects:
        if not project.samples:
            continue
        for sample in project.samples:
            if not sample.subsample or len(sample.subsample) == 0:
                continue
            for subsample in sample.subsample:
                if subsample.scan:
                    # Add an entry with scan count
                    project_items.append(
                        ProjectItem(
                            scan=len(subsample.scan),
                            subsample=subsample,
                            sample=sample,
                            project=project,
                        )
                    )
                else:
                    # Add an entry with no scans
                    project_items.append(
                        ProjectItem(
                            scan=0, subsample=subsample, sample=sample, project=project
                        )
                    )

    # Sort project_items by subsample.updatedAt in descending order to show most recent scans first
    project_items.sort(key=lambda item: item.subsample.updatedAt, reverse=True)

    context: Dict[str, Any] = {
        "request": request,
        "user": _user,
        "project_items": project_items,
    }
    return templates.TemplateResponse("projects.html", context)


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
