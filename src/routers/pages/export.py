from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, Response

from Models import TaskReq
from config_rdr import config
from helpers.auth import get_current_user_from_credentials
from local_DB.db_dependencies import get_db
from local_DB.models import User
from helpers.logger import logger
from providers.ecotaxa_client import EcoTaxaApiClient
from routers.pages.common import templates
from routers.tasks import create_task

# Create a router instance
router = APIRouter()


@router.get("/export_form", response_class=HTMLResponse)
def get_export_form(
    request: Request,
    project_id: str = Query(...),
    sample_id: str = Query(...),
    subsample_id: str = Query(...),
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Render the export form page.

    Args:
        request (Request): The FastAPI request object
        project_id (str): The project ID
        sample_id (str): The sample ID
        subsample_id (str): The subsample ID
        _user (User): The authenticated user
        db (Session): The database session

    Returns:
        HTMLResponse: The rendered HTML template
    """
    logger.info(
        f"Rendering export form for project_id={project_id}, sample_id={sample_id}, subsample_id={subsample_id}"
    )

    context = {
        "request": request,
        "user": _user,
        "project_id": project_id,
        "sample_id": sample_id,
        "subsample_id": subsample_id,
    }

    return templates.TemplateResponse("export.html", context)


@router.post("/export", response_class=HTMLResponse)
def export_scan(
    request: Request,
    project_id: str = Form(...),
    sample_id: str = Form(...),
    subsample_id: str = Form(...),
    ecotaxa_email: str = Form(...),
    ecotaxa_password: str = Form(...),
    task_to_create: str = Form(None),
    ecotaxa_project_id: str = Form(None),
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> Response:
    """
    Export the corresponding scan to EcoTaxa.

    Args:
        request (Request): The FastAPI request object
        project_id (str): The project ID
        sample_id (str): The sample ID
        subsample_id (str): The subsample ID
        ecotaxa_email (str): The EcoTaxa account email
        ecotaxa_password (str): The EcoTaxa account password
        task_to_create (str, optional): If present, create the export task
        ecotaxa_project_id (str, optional): The selected EcoTaxa project ID from the dropdown
        _user (User): The authenticated user
        db (Session): The database session

    Returns:
        HTMLResponse: The rendered HTML template or a redirect to the task monitoring page
    """

    logger.info(
        f"Received submission for project_id={project_id}, sample_id={sample_id}, subsample_id={subsample_id} with EcoTaxa credentials for {ecotaxa_email}"
    )

    # Validate EcoTaxa credentials
    try:
        ecotaxa_url = config.ECOTAXA_SERVER
        client = EcoTaxaApiClient(logger, ecotaxa_url, ecotaxa_email, ecotaxa_password)
        token = client.login()

        if token is None:
            # Authentication failed, return to the form with an error message
            context = {
                "request": request,
                "user": _user,
                "project_id": project_id,
                "sample_id": sample_id,
                "subsample_id": subsample_id,
                "error": "Invalid EcoTaxa credentials. Please try again.",
            }
            return templates.TemplateResponse("export.html", context)

        # Set the token for subsequent API calls
        client.token = token

    except Exception as e:
        # Error occurred during authentication, return to the form with an error message
        context = {
            "request": request,
            "user": _user,
            "project_id": project_id,
            "sample_id": sample_id,
            "subsample_id": subsample_id,
            "error": f"Error connecting to EcoTaxa: {str(e)}",
        }
        return templates.TemplateResponse("export.html", context)

    # If task_to_create is not present, show the authenticated state with projects list
    if not task_to_create:
        try:
            # Get the list of Zooscan projects
            projects = client.list_zooscan_projects()

            # Return the template with the authenticated state
            context = {
                "request": request,
                "user": _user,
                "project_id": project_id,
                "sample_id": sample_id,
                "subsample_id": subsample_id,
                "authenticated": True,
                "ecotaxa_email": ecotaxa_email,
                "ecotaxa_password": ecotaxa_password,
                "projects": projects,
            }
            return templates.TemplateResponse("export.html", context)
        except Exception as e:
            # Error occurred while fetching projects
            context = {
                "request": request,
                "user": _user,
                "project_id": project_id,
                "sample_id": sample_id,
                "subsample_id": subsample_id,
                "error": f"Error fetching projects from EcoTaxa: {str(e)}",
            }
            return templates.TemplateResponse("export.html", context)

    # Create a task of type "UPLOAD"
    task_req = TaskReq(
        exec="UPLOAD",
        params={
            "project": project_id,
            "sample": sample_id,
            "subsample": subsample_id,
            "ecotaxa_token": token,
            "ecotaxa_project_id": ecotaxa_project_id,
        },
    )

    # Submit the task
    task_response = create_task(task_req, _user, db)

    # Redirect to the task monitoring page
    return RedirectResponse(
        url=f"/ui/tasks/{task_response.id}", status_code=303  # HTTP 303 See Other
    )
