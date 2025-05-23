#
# Transformers from Legacy data to modern models
#
from pathlib import Path

from Models import Project, Drive


def project_from_legacy(drive_model: Drive, a_prj_path: Path, serial_number: str):
    unq_id = f"{drive_model.name}|{a_prj_path.name}"
    project = Project(
        path=str(a_prj_path),
        id=unq_id,
        name=a_prj_path.name,
        instrumentSerialNumber=serial_number,
        drive=drive_model,
    )
    return project
