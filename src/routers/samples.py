from pathlib import Path
from typing import List

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from Models import Sample, SampleWithBackRef
from ZooProcess_lib.ZooscanFolder import ZooscanDrive
from auth import get_current_user_from_credentials
from local_DB.db_dependencies import get_db
from logger import logger
from modern.from_legacy import (
    project_from_legacy,
    samples_from_legacy_project,
    sample_from_legacy,
)
from remote.DB import DB
from .utils import validate_path_components

# Create a router instance
router = APIRouter(
    prefix="/projects/{project_hash}/samples",
    tags=["samples"],
)


@router.get("")
def get_samples(
    project_hash: str,
    # user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
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
    zoo_drive, zoo_project, _, _ = validate_path_components(db, project_hash)
    logger.info(f"Getting samples for project {zoo_project.name}")

    return samples_from_legacy_project(db, zoo_project)


@router.get("/{sample_hash}")
def get_sample(
    project_hash: str,
    sample_hash: str,
    _user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> SampleWithBackRef:
    """
    Get a specific sample from a project.

    Args:
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample to get.

    Returns:
        Sample: The requested sample, including its parent project.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    # Validate the project and sample hashes
    zoo_drive, zoo_project, sample_name, _ = validate_path_components(
        db, project_hash, sample_hash
    )
    logger.info(f"Getting sample {sample_name} for project {zoo_project.name}")

    project = project_from_legacy(db, zoo_project.path)
    reduced = sample_from_legacy(db, zoo_project, sample_name)
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
    db: Session = Depends(get_db),
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
    # Validate the project hash
    zoo_drive, zoo_project, _, _ = validate_path_components(db, project_hash)
    logger.info(f"Creating sample for project {zoo_project.name}")

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # In a real implementation, you would save the sample to a database
    # For now, we'll just return the sample with a generated ID
    if not sample.id:
        sample.id = f"sample_{len(get_samples(project_hash, db)) + 1}"

    # Try to create the sample in the database
    # This is a placeholder - in a real implementation, you would save the sample to a database
    # For example: created_sample = db_instance.post(f"/projects/{project_hash}/samples", sample.dict())
    # For now, we'll just return the sample
    created_sample = sample

    return created_sample


@router.put("/{sample_hash}")
def update_sample(
    project_hash: str,
    sample_hash: str,
    sample: Sample,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> Sample:
    """
    Update a specific sample in a project.

    Args:
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample to update.
        sample (Sample): The updated sample data.

    Returns:
        Sample: The updated sample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    # Validate the project and sample hashes
    zoo_drive, zoo_project, sample_name, _ = validate_path_components(
        db, project_hash, sample_hash
    )
    logger.info(f"Updating sample {sample_name} for project {zoo_project.name}")

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Ensure the sample ID matches the path parameter
    if sample.id != sample_name:
        raise HTTPException(
            status_code=400,
            detail="Sample ID in the request body does not match the ID in the URL",
        )

    # Try to update the sample in the database
    # This is a placeholder - in a real implementation, you would update the sample in a database
    # For example: updated_sample = db_instance.put(f"/projects/{project_hash}/samples/{sample_hash}", sample.dict())
    # For now, we'll just return the sample
    updated_sample = sample

    return updated_sample


@router.delete("/{sample_hash}")
def delete_sample(
    project_hash: str,
    sample_hash: str,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete a specific sample from a project.

    Args:
        project_hash (str): The ID of the project.
        sample_hash (str): The hash of the sample to delete.

    Returns:
        dict: A message indicating the sample was deleted.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    # Validate the project and sample hashes
    zoo_drive, zoo_project, sample_name, _ = validate_path_components(
        db, project_hash, sample_hash
    )
    logger.info(f"Deleting sample {sample_name} for project {zoo_project.name}")

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to delete the sample from the database
    # This is a placeholder - in a real implementation, you would delete the sample from a database
    # For example: db_instance.delete(f"/projects/{project_hash}/samples/{sample_hash}")
    # For now, we'll just return a success message
    return {"message": f"Sample {sample_name} deleted from project {zoo_project.name}"}


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
