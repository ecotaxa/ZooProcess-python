from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pathlib import Path
from sqlalchemy.orm import Session

from Models import Sample, SampleWithBackRef, User
from auth import get_current_user_from_credentials
from ZooProcess_lib.ZooscanFolder import ZooscanDrive
from modern.ids import drive_and_project_from_hash
from modern.from_legacy import (
    project_from_legacy,
    samples_from_legacy_project,
    drive_from_legacy,
    sample_from_legacy,
)
from routers.projects import get_project_by_hash
from helpers.web import raise_404
from remote.DB import DB
from logger import logger
from local_DB.db_dependencies import get_db
import requests

# Create a router instance
router = APIRouter(
    prefix="/projects/{project_hash}/samples",
    tags=["samples"],
)


@router.get("")
def get_samples(
    project_hash: str,
    user=Depends(get_current_user_from_credentials),
) -> List[Sample]:
    """
    Get the list of samples associated with a project.

    Args:
        project_hash (str): The hash of the project to get samples for.

    Returns:
        List[Sample]: A list of samples associated with the project.

    Raises:
        HTTPException: If the project is not found or the user is not authorized.
    """
    logger.info(f"Getting samples for project {project_hash}")

    drive_path, project_name, _ = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    project = zoo_drive.get_project_folder(project_name)

    return samples_from_legacy_project(project)


@router.get("/{sample_id}")
def get_sample(
    project_hash: str,
    sample_id: str,
    # user=Depends(get_current_user_from_credentials),
    user: User = None,
) -> SampleWithBackRef:
    """
    Get a specific sample from a project.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to get.

    Returns:
        Sample: The requested sample, including its parent project.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Getting sample {sample_id} for project {project_hash}")

    drive_path, project_name, project_path = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    drive_model = drive_from_legacy(drive_path)

    zoo_project = zoo_drive.get_project_folder(project_name)

    # Check if the sample exists in the list of samples
    for sample_name in zoo_project.list_samples_with_state():
        if sample_name == sample_id:
            break
    else:
        raise_404(f"Sample with ID {sample_id} not found in project {project_hash}")
        sample_name = None  # Unreached

    project = project_from_legacy(drive_model, project_path)
    reduced = sample_from_legacy(zoo_project, sample_name)
    # Return the sample, enriched with back ref
    return SampleWithBackRef(
        **reduced.model_dump(),
        projectId=project.id,
        project=project,
    )


@router.post("")
def create_sample(
    project_hash: str,
    sample: Sample,
    user=Depends(get_current_user_from_credentials),
) -> Sample:
    """
    Add a new sample to a project.

    Args:
        project_hash (str): The ID of the project to add the sample to.
        sample (Sample): The sample data.

    Returns:
        Sample: The created sample.

    Raises:
        HTTPException: If the project is not found or the user is not authorized.
    """
    logger.info(f"Creating sample for project {project_hash}")

    # Check if the project exists
    drive_path, project_name, project_path = drive_and_project_from_hash(project_hash)

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # In a real implementation, you would save the sample to a database
    # For now, we'll just return the sample with a generated ID
    if not sample.id:
        sample.id = f"sample_{len(get_samples(project_hash, user)) + 1}"

    # Try to create the sample in the database
    # This is a placeholder - in a real implementation, you would save the sample to a database
    # For example: created_sample = db_instance.post(f"/projects/{project_hash}/samples", sample.dict())
    # For now, we'll just return the sample
    created_sample = sample

    return created_sample


def check_sample_exists(project_hash: str, sample_id: str, user: User = None):
    """
    Check if a sample exists in a project without retrieving all its data.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to check.
        user (User, optional): The user making the request. Defaults to None.

    Raises:
        HTTPException: If the sample is not found.
    """
    drive_path, project_name, _ = drive_and_project_from_hash(project_hash)
    zoo_drive = ZooscanDrive(drive_path)
    zoo_project = zoo_drive.get_project_folder(project_name)

    # Check if the sample exists in the list of samples
    for sample_name in zoo_project.list_samples_with_state():
        if sample_name == sample_id:
            return

    raise_404(f"Sample with ID {sample_id} not found in project {project_hash}")


@router.put("/{sample_id}")
def update_sample(
    project_hash: str,
    sample_id: str,
    sample: Sample,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> Sample:
    """
    Update a specific sample in a project.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to update.
        sample (Sample): The updated sample data.

    Returns:
        Sample: The updated sample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Updating sample {sample_id} for project {project_hash}")

    # Check if the project exists
    try:
        project = get_project_by_hash(project_hash, user)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        check_sample_exists(project_hash, sample_id, user)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Ensure the sample ID matches the path parameter
    if sample.id != sample_id:
        raise HTTPException(
            status_code=400,
            detail="Sample ID in the request body does not match the ID in the URL",
        )

    # Try to update the sample in the database
    # This is a placeholder - in a real implementation, you would update the sample in a database
    # For example: updated_sample = db_instance.put(f"/projects/{project_hash}/samples/{sample_id}", sample.dict())
    # For now, we'll just return the sample
    updated_sample = sample

    return updated_sample


@router.delete("/{sample_id}")
def delete_sample(
    project_hash: str,
    sample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> dict:
    """
    Delete a specific sample from a project.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to delete.

    Returns:
        dict: A message indicating the sample was deleted.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Deleting sample {sample_id} for project {project_hash}")

    # Check if the project exists
    try:
        project = get_project_by_hash(project_hash, user)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        check_sample_exists(project_hash, sample_id, user)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to delete the sample from the database
    # This is a placeholder - in a real implementation, you would delete the sample from a database
    # For example: db_instance.delete(f"/projects/{project_hash}/samples/{sample_id}")
    # For now, we'll just return a success message
    return {"message": f"Sample {sample_id} deleted from project {project_hash}"}


def postSample(projectId, sample, bearer, db):
    # url = f"{dbserver.getUrl()}/projects"
    url = f"{db}/projects/{projectId}/samples"
    logger.info(f"url: {url}")

    headers = {"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"}

    response = requests.post(url, json=sample, headers=headers)

    if response.status_code != 200:
        logger.error(f"response: {response}")
        logger.error(f"response text: {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail="Error importing sample: " + response.text,
        )

    logger.info(f"response: {response}")
    logger.info(f"response: {response.status_code}")

    sampleid = response.json().get("id")
    return sampleid
