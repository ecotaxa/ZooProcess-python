#
# Transformers from Legacy data to modern models
#
import os
from datetime import datetime
from pathlib import Path

from Models import Project, Drive, Sample, Background, User, Instrument
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder, ZooscanDrive
from modern.utils import (
    extract_serial_number,
    parse_sample_name,
    find_latest_modification_time,
)


def project_from_legacy(
    drive_model: Drive, a_prj_path: Path, serial_number: str = None
):
    unq_id = f"{drive_model.name}|{a_prj_path.name}"

    # Extract serial number from project name if not provided
    if serial_number is None:
        serial_number = extract_serial_number(a_prj_path.name)

    zoo_project = ZooscanDrive(Path(drive_model.url)).get_project_folder(
        a_prj_path.name
    )
    sample_models = samples_from_legacy_project(zoo_project)
    # Get the creation time of the directory
    creation_time = datetime.fromtimestamp(os.path.getmtime(a_prj_path))

    # Find the most recent modification time of any file in the project directory
    latest_mtime = find_latest_modification_time(a_prj_path)

    project = Project(
        path=str(a_prj_path),
        id=unq_id,
        name=a_prj_path.name,
        instrumentSerialNumber=serial_number,
        drive=drive_model,
        samples=sample_models,
        createdAt=creation_time,
        updatedAt=latest_mtime,
    )
    return project


def samples_from_legacy_project(project: ZooscanProjectFolder) -> list[Sample]:
    # In a real implementation, you would fetch the samples from a database
    # For now, we'll return a mock list of samples
    samples = []
    for sample_name in project.zooscan_scan.list_samples_with_state():
        # Parse the sample name into components
        parsed_name = parse_sample_name(sample_name)

        # Create metadata from parsed components
        metadata = []
        for key, value in parsed_name.items():
            if key not in ["full_name", "components", "num_components"]:
                metadata.append(
                    {
                        "id": f"{sample_name}_{key}",
                        "name": key,
                        "value": str(value),
                        "description": f"Extracted from sample name: {key}",
                    }
                )

        # Create the sample with metadata
        samples.append(Sample(id=sample_name, name=sample_name, metadata=metadata))
    return samples


def backgrounds_from_legacy_project(project: ZooscanProjectFolder) -> list[Background]:
    """
    Extract background information from a ZooscanProjectFolder and return a list of Background objects.

    Args:
        project (ZooscanProjectFolder): The project folder to extract backgrounds from.

    Returns:
        list[Background]: A list of Background objects representing the backgrounds in the project.
    """
    backgrounds = []

    # Get the background folder from the project
    back_folder = project.zooscan_back

    # Get all dates for which backgrounds exist
    dates = back_folder.get_dates()

    # Create a mock user and instrument for the backgrounds
    # In a real implementation, these would be fetched from a database
    mock_user = User(id="user1", name="n/a", email="user@example.com")
    mock_instrument = Instrument(
        id="instrument1",
        model="Zooscan",
        name="Default Zooscan",
        sn=extract_serial_number(project.project),
    )

    # For each date, create a Background object. Dates are in ZooProcess format
    for a_date in dates:
        # Get the background entry for this date
        entry = back_folder.content[a_date]

        # If there's a final background, add it to the list
        if entry["final_background"]:
            background_path = entry["final_background"]
            background_id = f"{a_date}"
            background_name = f"{a_date}_background"
            background_url = str(background_path)

            api_date = datetime.strptime(a_date, "%Y%m%d_%H%M")
            # Create the Background object
            background = Background(
                id=background_id,
                name=background_url,  # TODO: Tell frontend owner there is an invert here
                url=background_name,
                user=mock_user,
                instrument=mock_instrument,
                createdAt=api_date,
            )

            backgrounds.append(background)

    return backgrounds
