#
# Transformers from Legacy data to modern models
#
import os
from datetime import datetime
from pathlib import Path

from Models import Project, Drive, Sample
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
