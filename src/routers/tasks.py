from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Models import TaskRsp
from helpers.auth import get_current_user_from_credentials
from helpers.logger import logger
from helpers.web import raise_500, raise_404
from local_DB.db_dependencies import get_db
from local_DB.models import User
from modern.tasks import JobScheduler
from modern.utils import job_to_task_rsp

# Create a router instance with prefix "/task"
router = APIRouter(
    prefix="/task",
    tags=["tasks"],
)


@router.get("/{task_id}")
def get_task(
    task_id: str,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> TaskRsp:
    """
    Get a task by ID.

    This endpoint returns a TaskRsp based on the job with the provided ID.
    If no job with the provided ID is found, returns a default TaskRsp.

    Args:
        task_id (str): The ID of the task to retrieve.

    Returns:
        TaskRsp: A TaskRsp representing the job status and information.
    """
    logger.info(f"Received request to get task with ID: {task_id}")

    try:
        # Try to convert task_id to int for JobScheduler.get_job
        job_id = int(task_id)
        job = JobScheduler.get_job(job_id)
        if job is not None:
            # If job exists, use job_to_task_rsp to create TaskRsp
            return job_to_task_rsp(job)
        else:
            raise_404(f"{task_id} not found")
    except (ValueError, TypeError):
        # If task_id is not a valid integer, continue to default response
        raise_500(f"Invalid task ID format: {task_id}")
    assert False
