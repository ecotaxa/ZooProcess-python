#
# Transformers from modern models to Legacy data
#
from pathlib import Path
from logger import logger


def add_subsample(
    project_path: Path, sample_name: str, subsample_name: str, id1: str, data: dict
):
    """Add a subsample, in legacy filesystem, to a sample"""
    logger.info(
        f"Adding subsample with parameters: project_path={project_path}, sample_name={sample_name}, subsample_name={subsample_name}, id1={id1}, data={data}"
    )
