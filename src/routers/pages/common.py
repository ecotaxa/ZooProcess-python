from pathlib import Path
from typing import Any, NamedTuple

from fastapi.templating import Jinja2Templates


class ProjectItem(NamedTuple):
    """
    A flattened representation of project data including scan, subsample, sample, and project information.
    """

    scan: Any  # Scan object or count
    subsample: Any  # SubSample object
    sample: Any  # Sample object
    project: Any  # Project object


# Define the templates directory
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))
