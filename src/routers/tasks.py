from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from Models import TaskRsp, TaskReq
from helpers.auth import get_current_user_from_credentials
from helpers.web import raise_500, raise_404, raise_501
from local_DB.db_dependencies import get_db
from local_DB.models import User
from logger import logger
from modern.jobs.process import BackgroundAndScanToSegmented
from modern.tasks import JobScheduler
from modern.utils import job_to_task_rsp
from routers.utils import validate_path_components

# Create a router instance with prefix "/task"
router = APIRouter(
    prefix="/task",
    tags=["tasks"],
)


@router.post("")
def create_task(
    task: TaskReq,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> TaskRsp:
    """
    Create a new task.

    This endpoint receives a Task model but does nothing with it.
    It simply returns the received task.

    Args:
        task (TaskReq): The task creation data.

    Returns:
        TaskRsp: The received task.
    """
    logger.info(f"Received task: {task}")
    # e.g.   exec: 'PROCESS',
    #   params: {
    #     project: 'zooscan_lov|Zooscan_triatlas_m158_2019_mtn_200microns_sn001',
    #     sample: 'm158_mn03_n1',
    #     subsample: 'zooscan_lov|Zooscan_triatlas_m158_2019_mtn_200microns_sn001_undefined',
    #     scanId: 'zooscan_lov|Zooscan_triatlas_m158_2019_mtn_200microns_sn001_undefined_1'
    # e.g.: exec='BACKGROUND'
    #   params:
    #     'project': 'zooscan_lov|Zooscan_triatlas_m158_2019_mtn_200microns_sn001',
    #     'instrumentId': 'sn001',
    #     'background': ['http://localhost:5000/projects/zooscan_lov|Zooscan_ptb_jb_1974_a_1979_LARGE_sn174/background/20240527_0759_fnl.jpg',
    #     'http://localhost:5000/projects/zooscan_lov|Zooscan_ptb_jb_1974_a_1979_LARGE_sn174/background/20240527_0759_fnl.jpg']

    if task.exec == "PROCESS":
        params = task.params
        # Note: params["scanId"] is ignored
        project_hash, sample_hash, subsample_hash = (
            params["project"],
            params["sample"],
            params["subsample"],
        )
        zoo_drive, zoo_project, sample_name, subsample_name = validate_path_components(
            db, project_hash, sample_hash, subsample_hash
        )
        new_task = BackgroundAndScanToSegmented(
            zoo_project, sample_name, subsample_name
        )
        JobScheduler.submit(new_task)
        logger.info(f"Processing task: {task}")
        # Use job_to_task_rsp to create TaskRsp from the job
        return job_to_task_rsp(new_task)
    raise_501(f"Task.exec not implemented: {task.exec}")
    assert False


COUNTER = 0


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


@router.post("/{task_id}/run")
def run_task(
    task_id: str,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> Response:
    """
    Run a task.

    This endpoint does nothing and simply returns a success response.

    Args:
        task_id (str): The ID of the task to run.

    Returns:
        Response: A success response with status code 200.
    """
    logger.info(f"Received request to run task with ID: {task_id}")
    return Response(status_code=status.HTTP_200_OK)
