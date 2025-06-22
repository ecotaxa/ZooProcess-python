from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from Models import TaskRsp
from helpers.auth import get_current_user_from_credentials
from local_DB.db_dependencies import get_db
from local_DB.models import User
from logger import logger
from routers.pages.common import templates

# Create a router instance
router = APIRouter()


@router.get("/tasks/{task_id}", response_class=HTMLResponse)
def get_task_page(
    task_id: str,
    request: Request,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Serve the task details page for a specific task.

    Args:
        task_id (str): The ID of the task to display
        request (Request): The FastAPI request object
        _user (User): The authenticated user
        db (Session): The database session

    Returns:
        HTMLResponse: The rendered HTML template with task details
    """
    from routers.tasks import get_task

    logger.info(f"Serving task page for task_id: {task_id}")

    # Get task data using the API
    task = get_task(task_id=task_id, _user=_user, db=db)

    # Extract task statuses from TaskRsp for template use
    task_statuses = {
        "PENDING": "PENDING",
        "RUNNING": "RUNNING",
        "FINISHED": "FINISHED",
        "FAILED": "FAILED",
    }

    context: Dict[str, Any] = {
        "request": request,
        "user": _user,
        "task": task,
        "task_statuses": task_statuses,
    }
    return templates.TemplateResponse("task.html", context)
