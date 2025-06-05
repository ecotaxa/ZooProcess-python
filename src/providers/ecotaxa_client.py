import requests
from .ProjectModel import ProjectModel


def get_project(
    project_id: int, bearer: str, api_base_url: str = "https://ecotaxa.obs-vlfr.fr/api"
) -> ProjectModel:
    """
    Fetch project details from EcoTaxa API and return as ProjectModel
    """

    headers = {"Authorization": f"Bearer {bearer}"}

    url = f"{api_base_url}/projects/{project_id}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raises exception for 4XX/5XX status codes

    # Convert response data to ProjectModel
    project_data = response.json()
    return ProjectModel(**project_data)
