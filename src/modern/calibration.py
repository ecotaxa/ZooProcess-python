from typing import Dict, List

from fastapi import HTTPException

from src.remote_db.DB import DB
from src.Models import Calibration


def create(instrumentId: str, calibration: Dict, db: DB) -> Calibration:
    """
    Create a new calibration for an instrument.

    Args:
        instrumentId (str): The ID of the instrument to add the calibration to.
        calibration (Dict): The calibration data.
        db (DB): The database connection.

    Returns:
        Calibration: The created calibration.

    Raises:
        HTTPException: If the calibration could not be created.
    """
    try:
        # Add the calibration to the database
        created_calibration = db.post(
            f"/instruments/{instrumentId}/calibration", calibration
        )
        return Calibration(**created_calibration)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create calibration: {str(e)}"
        )


def update(calibrationId: str, calibration: Dict, db: DB) -> Calibration:
    """
    Update an existing calibration.

    Args:
        calibrationId (str): The ID of the calibration to update.
        calibration (Dict): The updated calibration data.
        db (DB): The database connection.

    Returns:
        Calibration: The updated calibration.

    Raises:
        HTTPException: If the calibration could not be updated.
    """
    try:
        # Update the calibration in the database
        updated_calibration = db.put(f"/calibrations/{calibrationId}", calibration)
        return Calibration(**updated_calibration)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update calibration: {str(e)}"
        )


def get_by_id(calibrationId: str, db: DB) -> Calibration:
    """
    Get a calibration by its ID.

    Args:
        calibrationId (str): The ID of the calibration to retrieve.
        db (DB): The database connection.

    Returns:
        Calibration: The calibration with the specified ID.

    Raises:
        HTTPException: If the calibration could not be found.
    """
    try:
        # Get the calibration from the database
        calibration = db.get(f"/calibrations/{calibrationId}")
        return Calibration(**calibration)
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Calibration with ID {calibrationId} not found"
        )


def get_by_instrument(instrumentId: str, db: DB) -> List[Calibration]:
    """
    Get all calibrations for an instrument.

    Args:
        instrumentId (str): The ID of the instrument to get calibrations for.
        db (DB): The database connection.

    Returns:
        List[Calibration]: A list of calibrations for the instrument.

    Raises:
        HTTPException: If the calibrations could not be retrieved.
    """
    try:
        # Get the calibrations from the database
        calibrations = db.get(f"/instruments/{instrumentId}/calibrations")
        return [Calibration(**calibration) for calibration in calibrations]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve calibrations: {str(e)}"
        )
