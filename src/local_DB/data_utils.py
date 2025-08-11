"""
Utility functions for working with the local database.
"""

from typing import Optional

from sqlalchemy.orm import Session

from .models import ScanBackground


def get_background_id(
    db: Session, drive_name: str, project_name: str, scan_id: str
) -> Optional[str]:
    """
    Get the background_id for a scan identified by its primary key.

    Args:
        db: The database session.
        drive_name (str): The drive name component of the primary key.
        project_name (str): The project name component of the primary key.
        scan_id (str): The scan ID component of the primary key.

    Returns:
        str: The background_id if found, None otherwise.
    """
    scan_background = (
        db.query(ScanBackground)
        .filter_by(drive_name=drive_name, project_name=project_name, scan_id=scan_id)
        .first()
    )

    if scan_background:
        return scan_background.background_id
    return None


def set_background_id(
    db: Session, drive_name: str, project_name: str, scan_id: str, background_id: str
) -> None:
    """
    Set the background_id for a scan identified by its primary key.

    Args:
        db: The database session.
        drive_name (str): The drive name component of the primary key.
        project_name (str): The project name component of the primary key.
        scan_id (str): The scan ID component of the primary key.
        background_id (str): The background ID to set.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    # Check if a ScanBackground record already exists
    scan_background = (
        db.query(ScanBackground)
        .filter_by(drive_name=drive_name, project_name=project_name, scan_id=scan_id)
        .first()
    )

    if scan_background:
        # Update existing record
        scan_background.background_id = background_id
    else:
        # Create new record
        scan_background = ScanBackground(
            drive_name=drive_name,
            project_name=project_name,
            scan_id=scan_id,
            background_id=background_id,
        )
        db.add(scan_background)

    db.commit()
