from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from helpers.auth import get_current_user_from_credentials
from local_DB.db_dependencies import get_db
from local_DB.models import User
from logger import logger
from routers.pages.common import templates, ProjectItem
from routers.projects import get_projects as api_get_projects

# Create a router instance
router = APIRouter()


@router.get("/projects", response_class=HTMLResponse)
def get_projects_page(
    request: Request,
    _user: User = Depends(get_current_user_from_credentials),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Serve the projects page with a list of ProjectItem NamedTuples containing scan, subsample, sample, and project information.
    Samples without subsamples are discarded.

    Args:
        request (Request): The FastAPI request object
        _user (User): The authenticated user
        db (Session): The database session

    Returns:
        HTMLResponse: The rendered HTML template
    """
    logger.info("Serving projects page")
    # Get projects data using the API
    projects = api_get_projects(_user=_user, db=db)

    # Transform the tree structure into a list of ProjectItem objects
    project_items: List[ProjectItem] = []

    for project in projects:
        if not project.samples:
            continue
        for sample in project.samples:
            if not sample.subsample or len(sample.subsample) == 0:
                continue
            for subsample in sample.subsample:
                if subsample.scan:
                    # Add an entry with scan count
                    project_items.append(
                        ProjectItem(
                            scan=len(subsample.scan),
                            subsample=subsample,
                            sample=sample,
                            project=project,
                        )
                    )
                else:
                    # Add an entry with no scans
                    project_items.append(
                        ProjectItem(
                            scan=0, subsample=subsample, sample=sample, project=project
                        )
                    )

    # Sort project_items by subsample.updatedAt in descending order to show most recent scans first
    project_items.sort(key=lambda item: item.subsample.updatedAt, reverse=True)

    context: Dict[str, Any] = {
        "request": request,
        "user": _user,
        "project_items": project_items,
    }
    return templates.TemplateResponse("projects.html", context)
