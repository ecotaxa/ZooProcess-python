from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from Models import Instrument, Calibration, Background, Project
from auth import get_current_user_from_credentials
from modern.instrument import get_instruments as get_all_instruments
from modern.instrument import get_instrument_by_id
import modern.calibration as calibration_module
from remote.DB import DB
from local_DB.db_dependencies import get_db
from logger import logger

# Create a router instance
router = APIRouter(
    prefix="/instruments",
    tags=["instruments"],
)


@router.get("")
def get_instruments(full: bool = False):
    """
    Returns a list of all instruments.

    Args:
        full (bool, optional): If True, returns the full instrument details. Defaults to False.
    """

    instruments = get_all_instruments()

    if not full:
        # Return a simplified version with just id and name
        return [
            {"id": instrument.id, "name": instrument.name} for instrument in instruments
        ]

    return instruments


@router.get("/{instrument_id}")
def get_instrument(instrument_id: str):
    """
    Returns details about a specific instrument.

    Args:
        instrument_id (str): The ID of the instrument to retrieve.

    Returns:
        Instrument: The instrument with the specified ID.

    Raises:
        HTTPException: If the instrument is not found.
    """

    instrument = get_instrument_by_id(instrument_id)
    if instrument is None:
        raise HTTPException(
            status_code=404, detail=f"Instrument with ID {instrument_id} not found"
        )
    return instrument


@router.get("/{instrument_id}/backgrounds")
def get_backgrounds_by_instrument(instrument_id: str) -> List[Background]:
    """
    Returns the last scanned backgrounds for a given instrument.

    Args:
        instrument_id (str): The ID of the instrument to retrieve backgrounds for.

    Returns:
        List[Background]: A list of backgrounds associated with the instrument.

    Raises:
        HTTPException: If the instrument is not found.
    """

    # Check if the instrument exists
    instrument = get_instrument_by_id(instrument_id)
    if instrument is None:
        raise HTTPException(
            status_code=404, detail=f"Instrument with ID {instrument_id} not found"
        )

    # Get all projects
    from routers.projects import list_all_projects
    from config_rdr import config
    from collections import OrderedDict
    from pathlib import Path
    from ZooProcess_lib.ZooscanFolder import ZooscanDrive
    from modern.from_legacy import backgrounds_from_legacy_project

    projects = list_all_projects(config.DRIVES)

    # Collect all backgrounds from all projects
    all_backgrounds = OrderedDict()
    a_project: Project
    for a_project in projects:
        if a_project.instrument.id != instrument_id:
            continue
        zoo_drive = ZooscanDrive(Path(a_project.drive.url))
        project_folder = zoo_drive.get_project_folder(a_project.name)
        # Get backgrounds for this project
        project_backgrounds = backgrounds_from_legacy_project(project_folder)
        # Add to the list
        for a_bg in project_backgrounds:
            if a_bg.id not in all_backgrounds:
                all_backgrounds[a_bg.id] = a_bg

    # Sort by creation date (newest first)
    ret = list(all_backgrounds.values())
    ret.sort(key=lambda bg: bg.createdAt, reverse=True)

    return ret


@router.put("/{instrument_id}/calibration/{calibrationId}")
def update_calibration(
    instrument_id: str,
    calibrationId: str,
    calibration: Calibration,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
):
    """
    Update a calibration.

    Args:
        instrument_id (str): The ID of the instrument which owns the calibration.
        calibrationId (str): The ID of the calibration to update.
        calibration (Calibration): The updated calibration data.

    Returns:
        Calibration: The updated calibration.

    Raises:
        HTTPException: If the calibration is not found or the user is not authorized.
    """

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Update the calibration
    return calibration_module.update(calibrationId, calibration.dict(), db_instance)


@router.post("/{instrument_id}/calibration")
def create_calibration(
    instrument_id: str,
    calibration: Calibration,
    user=Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
):
    """
    Add a calibration to an instrument.

    Args:
        instrument_id (str): The ID of the instrument to add the calibration to.
        calibration (Calibration): The calibration data.

    Returns:
        Calibration: The created calibration.

    Raises:
        HTTPException: If the instrument is not found or the user is not authorized.
    """
    # Check if the instrument exists

    instrument = get_instrument_by_id(instrument_id)
    if instrument is None:
        raise HTTPException(
            status_code=404, detail=f"Instrument with ID {instrument_id} not found"
        )

    # Create a DB instance
    db_instance = DB(bearer=user.id)

    # Create the calibration
    return calibration_module.create(instrument_id, calibration.dict(), db_instance)
