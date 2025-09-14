import importlib
import os
from pathlib import Path


HERE = Path(__file__).parent


def test_project_perf():
    """
    Performance test for project-related listing primitive.

    """
    os.environ["APP_ENV"] = "dev"
    os.chdir(HERE.parent)
    import config_rdr
    from local_DB.db_dependencies import get_db
    from routers.projects import list_all_projects

    # Get the list of projects using the actual implementation
    projects = list_all_projects(next(get_db()), config_rdr.config.get_drives(), 3)

    # Ensure we have at least one project to test with
    assert len(projects) > 0, "No projects found in the configured drives"
