from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from Models import SubSample, SubSampleIn, User
from auth import get_current_user_from_credentials
from modern.to_legacy import add_subsample
from routers.projects import get_project_by_hash
from routers.samples import get_sample
from helpers.web import raise_404
from remote.DB import DB
from logger import logger
from local_DB.db_dependencies import get_db

# Create a router instance
router = APIRouter(
    prefix="/projects/{project_hash}/samples/{sample_id}/subsamples",
    tags=["subsamples"],
)


@router.get("")
def get_subsamples(
    project_hash: str,
    sample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> List[SubSample]:
    """
    Get the list of subsamples associated with a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to get subsamples for.

    Returns:
        List[SubSample]: A list of subsamples associated with the sample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Getting subsamples for sample {sample_id} in project {project_hash}")

    # Check if the project exists
    try:
        project = get_project_by_hash(project_hash, user)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        sample = get_sample(project_hash, sample_id, user)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to get subsamples from the database
    # This is a placeholder - in a real implementation, you would fetch the subsamples from a database
    # For example: subsamples = db_instance.get(f"/projects/{project_hash}/samples/{sample_id}/subsamples")
    # For now, we'll return a mock list of subsamples
    subsample1 = SubSample(id="subsample1", name="Subsample 1")
    subsample2 = SubSample(id="subsample2", name="Subsample 2")
    subsamples = [subsample1, subsample2]

    return subsamples


@router.post("")
def create_subsample(
    project_hash: str,
    sample_id: str,
    subsample: SubSampleIn,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> SubSample:
    """
    Add a new subsample to a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample to add the subsample to.
        subsample (SubSampleIn): The subsample data containing name, metadataModelId, and additional data.
        user (User, optional): The authenticated user. Defaults to the current user from credentials.
        db (Session, optional): Database session. Defaults to the session from dependency.

    Returns:
        SubSample: The created subsample.

    Raises:
        HTTPException: If the project or sample is not found, or the user is not authorized.
    """
    logger.info(f"Creating subsample for sample {sample_id} in project {project_hash}")

    # Check if the project exists
    try:
        project = get_project_by_hash(project_hash, user)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        sample = get_sample(project_hash, sample_id, user)
    except HTTPException as e:
        raise e

    add_subsample(
        project.path,
        sample.name,
        subsample.name,
        subsample.metadataModelId,
        subsample.data,
    )
    ret = SubSample(
        id="subsample1", name="Subsample 1", scan=[], metadata=[]
    )  # TODO: a subsample_from_legacy primitive
    return ret


@router.get("/{subsample_id}")
def get_subsample(
    project_hash: str,
    sample_id: str,
    subsample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> SubSample:
    """
    Get a specific subsample from a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample.
        subsample_id (str): The ID of the subsample to get.

    Returns:
        SubSample: The requested subsample.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    logger.info(
        f"Getting subsample {subsample_id} for sample {sample_id} in project {project_hash}"
    )

    # Check if the project exists
    try:
        project = get_project_by_hash(project_hash, user)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        sample = get_sample(project_hash, sample_id, user)
    except HTTPException as e:
        raise e

    # Try to get the subsample from the database
    # This is a placeholder - in a real implementation, you would fetch the subsample from a database
    # For example: subsample = db_instance.get(f"/projects/{project_hash}/samples/{sample_id}/subsamples/{subsample_id}")
    # For now, we'll return a mock subsample
    subsample = SubSample(
        id=subsample_id, name=f"Subsample {subsample_id}", scan=[], metadata=[]
    )

    return subsample


@router.delete("/{subsample_id}")
def delete_subsample(
    project_hash: str,
    sample_id: str,
    subsample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> dict:
    """
    Delete a specific subsample from a sample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample.
        subsample_id (str): The ID of the subsample to delete.

    Returns:
        dict: A message indicating the subsample was deleted.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    logger.info(
        f"Deleting subsample {subsample_id} for sample {sample_id} in project {project_hash}"
    )

    # Check if the project exists
    try:
        project = get_project_by_hash(project_hash, user)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        sample = get_sample(project_hash, sample_id, user)
    except HTTPException as e:
        raise e

    # Check if the subsample exists
    try:
        subsample = get_subsample(project_hash, sample_id, subsample_id, user)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to delete the subsample from the database
    # This is a placeholder - in a real implementation, you would delete the subsample from a database
    # For example: db_instance.delete(f"/projects/{project_hash}/samples/{sample_id}/subsamples/{subsample_id}")
    # For now, we'll just return a success message
    pass

    return {"message": f"Subsample {subsample_id} deleted successfully"}


@router.get("/{subsample_id}/process")
def process_subsample(
    project_hash: str,
    sample_id: str,
    subsample_id: str,
    user=Depends(get_current_user_from_credentials),
) -> dict:
    """
    Process a specific subsample.

    Args:
        project_hash (str): The ID of the project.
        sample_id (str): The ID of the sample.
        subsample_id (str): The ID of the subsample to process.

    Returns:
        dict: A message indicating the subsample was processed.

    Raises:
        HTTPException: If the project, sample, or subsample is not found, or the user is not authorized.
    """
    logger.info(
        f"Processing subsample {subsample_id} for sample {sample_id} in project {project_hash}"
    )

    # Check if the project exists
    try:
        project = get_project_by_hash(project_hash, user)
    except HTTPException as e:
        raise e

    # Check if the sample exists
    try:
        sample = get_sample(project_hash, sample_id, user)
    except HTTPException as e:
        raise e

    # Check if the subsample exists
    try:
        subsample = get_subsample(project_hash, sample_id, subsample_id, user)
    except HTTPException as e:
        raise e

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Try to process the subsample
    # This is a placeholder - in a real implementation, you would process the subsample
    # For example: result = db_instance.get(f"/projects/{project_hash}/samples/{sample_id}/subsamples/{subsample_id}/process")
    # For now, we'll just return a success message
    result = {
        "status": "success",
        "message": f"Subsample {subsample_id} processed successfully",
    }

    return result
