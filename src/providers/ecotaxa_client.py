import requests
from .EcoTaxaProjectModel import ProjectModel
from config_rdr import config


def get_project(project_id: int, bearer: str, api_base_url: str = None) -> ProjectModel:
    """
    Fetch project details from EcoTaxa API and return as ProjectModel
    """
    if api_base_url is None:
        api_base_url = config.ECOTAXA_SERVER

    headers = {"Authorization": f"Bearer {bearer}"}

    url = f"{api_base_url}/projects/{project_id}"

    response = requests.get(url, headers=headers, timeout=(10, 600))
    response.raise_for_status()  # Raises exception for 4XX/5XX status codes

    # Convert response data to ProjectModel
    project_data = response.json()
    return ProjectModel(**project_data)
