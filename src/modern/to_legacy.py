#
# Transformers from modern models to Legacy data
#
from pathlib import Path


def add_subsample(
    project_path: Path, sample_name: str, subsample_name: str, id1: str, data: dict
):
    """Add a subsample, in legacy filesystem, to a sample"""
