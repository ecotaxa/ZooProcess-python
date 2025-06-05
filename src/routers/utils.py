from typing import Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ZooProcess_lib.ZooscanFolder import ZooscanDrive, ZooscanProjectFolder
from legacy.utils import find_scan_metadata
from modern.ids import (
    drive_and_project_from_hash,
    sample_name_from_sample_hash,
    subsample_name_from_hash,
)
from modern.subsample import get_project_scans_metadata


def validate_path_components(
    db: Session, *components
) -> Tuple[ZooscanDrive, ZooscanProjectFolder, str, str]:
    """
    Validate up to 3 parts of the path in endpoints (project, sample, subsample).

    Args:
        *components: Variable number of path components to validate.
            - First component (required): project_hash
            - Second component (optional): sample_hash
            - Third component (optional): subsample_hash
        db (Session, optional): SQLAlchemy database session for validating subsample existence.

    Returns:
        Tuple containing:
            - zoo_drive: ZooscanDrive object representing the drive
            - zoo_project: ZooscanProjectFolder object representing the project
            - sample_name: String representing the sample name (or None if not provided)
            - subsample_name: String representing the subsample name (or None if not provided)

    Raises:
        HTTPException: If any of the components are invalid or not found
        ValueError: If more than 3 components are provided
    """
    if len(components) > 3:
        raise ValueError(
            "Maximum 3 path components (project, sample, subsample) are supported"
        )

    if len(components) == 0:
        raise ValueError("At least one path component (project_hash) is required")

    # Validate project_hash (required)
    project_hash = components[0]
    drive_path, project_name = drive_and_project_from_hash(project_hash)

    # Create ZooscanDrive object
    zoo_drive = ZooscanDrive(drive_path)

    # Create ZooscanProjectFolder object
    zoo_project = zoo_drive.get_project_folder(project_name)

    # Initialize optional return values
    sample_name = ""
    subsample_name = ""

    # Validate sample_hash (optional)
    if len(components) > 1:
        sample_hash = components[1]
        sample_name = sample_name_from_sample_hash(sample_hash)

        # Check if the sample exists in the project

        for existing_sample_name in zoo_project.list_samples_with_state():
            if existing_sample_name == sample_name:
                break
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Sample with ID {sample_name} not found in project {project_hash}",
            )

    # Validate subsample_hash (optional)
    if len(components) > 2:
        subsample_hash = components[2]
        subsample_name = subsample_name_from_hash(subsample_hash)

        # Check if the subsample exists in the sample if db is provided
        if db is not None and sample_name is not None:

            # Get all scans metadata for the project
            scans_metadata = get_project_scans_metadata(db, zoo_project)

            # Check if the subsample exists in the sample
            if not find_scan_metadata(scans_metadata, sample_name, subsample_name):
                raise HTTPException(
                    status_code=404,
                    detail=f"Subsample with ID {subsample_name} not found in sample {sample_name}",
                )

    return zoo_drive, zoo_project, sample_name, subsample_name
