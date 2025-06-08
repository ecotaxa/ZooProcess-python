from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from Models import Task, TaskIn
from helpers.auth import get_current_user_from_credentials
from local_DB.db_dependencies import get_db
from local_DB.models import User
from logger import logger

# Create a router instance with prefix "/task"
router = APIRouter(
    prefix="/task",
    tags=["tasks"],
)


@router.post("")
def create_task(
    task: TaskIn,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> Task:
    """
    Create a new task.

    This endpoint receives a Task model but does nothing with it.
    It simply returns the received task.

    Args:
        task (TaskIn): The task creation data.

    Returns:
        Task: The received task.
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

    ret = Task(
        **task.model_dump(),
        id="1",
        percent=1,
        status="PENDING",
        log="task1log",
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
    )
    return ret


COUNTER = 0


@router.get("/{task_id}")
def get_task(
    task_id: str,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> Task:
    """
    Get a task by ID.

    This endpoint returns a hardcoded task with the provided ID.

    Args:
        task_id (str): The ID of the task to retrieve.

    Returns:
        Task: A hardcoded task with the provided ID.
    """
    logger.info(f"Received request to get task with ID: {task_id}")
    global COUNTER
    COUNTER += 1
    if COUNTER > 10:
        status = "FINISHED"
        COUNTER = 0
    else:
        status = "RUNNING"
    return Task(
        id=task_id,
        exec="process_images",
        params={"project_id": "123", "sample_id": "456"},
        percent=75,
        status=status,
        log="task_log_url",
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
    )


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
