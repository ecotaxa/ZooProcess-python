from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from helpers.auth import get_current_user_from_credentials
from local_DB.db_dependencies import get_db
from local_DB.models import User
from logger import logger

# Create a router instance
router = APIRouter()


@router.post("/export", response_class=HTMLResponse)
def export_scan(
    request: Request,
    project_id: str = Form(...),
    sample_id: str = Form(...),
    subsample_id: str = Form(...),
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Export corresponding scan to EcoTaxa.

    Args:
        request (Request): The FastAPI request object
        project_id (str): The project ID
        sample_id (str): The sample ID
        subsample_id (str): The subsample ID
        _user (User): The authenticated user
        db (Session): The database session

    Returns:
        HTMLResponse: The rendered HTML template or a redirect to the task monitoring page
    """
    from Models import TaskReq
    from routers.tasks import create_task

    logger.info(
        f"Received submission for project_id={project_id}, sample_id={sample_id}, subsample_id={subsample_id}"
    )

    # Create a task of type "UPLOAD"
    task_req = TaskReq(
        exec="UPLOAD",
        params={
            "project": project_id,
            "sample": sample_id,
            "subsample": subsample_id,
        },
    )

    # Submit the task
    task_response = create_task(task_req, _user, db)

    # Redirect to the task monitoring page
    return RedirectResponse(
        url=f"/ui/tasks/{task_response.id}", status_code=303  # HTTP 303 See Other
    )
