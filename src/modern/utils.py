import re
from calendar import EPOCH
from datetime import datetime
from os.path import getmtime
from pathlib import Path
from typing import Dict, List, Tuple

from Models import TaskRsp
from .tasks import Job, JobStateEnum

OLD_DATE = datetime(1970, 1, 1, 0, 0, 0)
FAR_DATE = datetime(9999, 12, 31, 23, 59, 59)


def min_max_dates(paths: List[Path]) -> Tuple[datetime, datetime]:
    """
    Find the minimum and maximum modification times for a list of Path objects.

    Args:
        paths: A list of Path objects to check

    Returns:
        A tuple of (min_time, max_time) as datetime objects
    """
    times = []
    # Process each path in the list
    for path in paths:
        try:
            # Get the modification time of the file or directory
            times.append(getmtime(path))
        except (OSError, PermissionError):
            # Skip files that can't be accessed or don't exist
            continue

    if len(times) == 0:
        return OLD_DATE, FAR_DATE

    return datetime.fromtimestamp(min(times)), datetime.fromtimestamp(max(times))


def extract_serial_number(project_name: str) -> str:
    """
    Extract the serial number (sn) from the project name.
    It can be in the end of the name or in the middle.
    Default to 'sn???' if not found.

    Args:
        project_name: The name of the project

    Returns:
        The extracted serial number or 'sn???' if not found
    """
    # Look for 'sn' followed by digits in the project name
    match = re.search(r"sn\d+", project_name.lower())
    if match:
        return match.group(0)
    return "sn???"


def parse_sample_name(sample_name: str) -> dict:
    """
    Parse a sample name into its components.
    Sample names follow the structure: [program]_[ship]_[net_type]_[optional_mesh_size]_[cruise_number]_st[station_id]_[day_night]_n[net_number]_d[fraction_type]_[fraction_id]_sur_[total_fractions]_[scan_number]
    Example: apero2023_tha_bioness_sup2000_017_st66_d_n1_d3_1_sur_4_1

    Components Breakdown:
    1. Program: Scientific program name, often with year (e.g., `apero2023`)
    2. Ship: Abbreviated ship name (e.g., `tha` for thalassa)
    3. Net Type: Type of sampling net (e.g., `bioness`)
    4. Optional Mesh Size: Sometimes includes mesh size (e.g., `sup2000`)
    5. Cruise Number: Numbered cruise identifier (e.g., `013`, `014`, `017`)
    6. Station ID: Station identifier with prefix (e.g., `st46`, `st66`)
    7. Day/Night: Sampling time - `d` (day) or `n` (night)
    8. Net Number: Specific net used with prefix (e.g., `n1`, `n2`, `n9`)
    9. Fraction Type: Type of fraction with prefix (e.g., `d1`, `d2`, `d3`)
    10. Fraction: Information about the fraction, including ID and total count (e.g., `1_sur_4`)
    11. Scan Number: Sequential scan number (typically `1`)

    Args:
        sample_name: The name of the sample

    Returns:
        A dictionary containing the parsed components of the sample name
    """
    components = sample_name.split("_")
    parsed = {}

    # Initialize component index
    idx = 0

    # Try to assign meaning to components based on position and patterns
    if idx < len(components):
        parsed["program"] = components[idx]
        idx += 1

    if idx < len(components):
        parsed["ship"] = components[idx]
        idx += 1

    if idx < len(components):
        parsed["net_type"] = components[idx]
        idx += 1

    # Check for optional mesh size (if present)
    if idx < len(components) and components[idx].startswith("sup"):
        parsed["mesh_size"] = components[idx]
        idx += 1

    if idx < len(components):
        parsed["cruise_number"] = components[idx]
        idx += 1

    if idx < len(components) and components[idx].startswith("st"):
        parsed["station_id"] = components[idx]
        idx += 1

    if idx < len(components) and (components[idx] == "d" or components[idx] == "n"):
        parsed["day_night"] = components[idx]
        idx += 1

    if idx < len(components) and components[idx].startswith("n"):
        parsed["net_number"] = components[idx]
        idx += 1

    if idx < len(components) and components[idx].startswith("d"):
        parsed["fraction_type"] = components[idx]
        idx += 1

    # Group fraction_id, total_fractions_prefix, and total_fractions into a single component
    if idx < len(components):
        fraction_id = components[idx]
        idx += 1

        # Check for "sur_X" pattern for total fractions
        if idx + 1 < len(components) and components[idx] == "sur":
            total_fractions_prefix = components[idx]
            idx += 1
            total_fractions = components[idx]
            idx += 1

            # Combine the components into a single fraction component
            parsed["fraction"] = (
                f"{fraction_id}_{total_fractions_prefix}_{total_fractions}"
            )
        else:
            # If no total fractions information, just use the fraction_id
            parsed["fraction"] = fraction_id

    if idx < len(components):
        parsed["scan_number"] = components[idx]

    return parsed


def convert_ddm_to_decimal_degrees(a_value):
    """
    Convert a coordinate from Degrees Decimal Minutes (DDM) format to Decimal Degrees (DD) format.

    In DDM format, the decimal part represents minutes divided by 100 (e.g., 45.30 means 45 degrees and 30 minutes).
    This function converts it to decimal degrees where minutes are divided by 60 (e.g., 45.5 degrees).

    The conversion formula is: DD = degrees + (minutes/60)
    Which is implemented as: degrees + (decimal_part * 100/60)/100

    Args:
        a_value: A coordinate value in DDM format (e.g., 45.30 for 45°30')

    Returns:
        The coordinate converted to decimal degrees format (e.g., 45.50 for 45.5°)
        If the input cannot be converted to a float, returns the original value.

    Examples:
        >>> convert_ddm_to_decimal_degrees(45.30)
        45.5
        >>> convert_ddm_to_decimal_degrees(10.3030)
        10.505
    """
    val = float(a_value)
    degrees = int(val)
    decimal = (val - degrees) * 100
    decimal = round(decimal / 30 * 50, 4)
    return degrees + decimal / 100


def job_to_task_rsp(job: Job) -> TaskRsp:
    """
    Transform a Job object into a TaskRsp model.

    Args:
        job: A Job object with properties like job_id, state, created_at, updated_at

    Returns:
        A TaskRsp model representing the job status and information

    Examples:
        >>> job = Job(1)
        >>> task_rsp = job_to_task_rsp(job)
    """

    # Map job state to task status
    status_map = {
        JobStateEnum.Pending: "PENDING",
        JobStateEnum.Running: "RUNNING",
        JobStateEnum.Error: "FAILED",
        JobStateEnum.Finished: "FINISHED",
    }

    # Calculate progress percentage based on job state
    percent = 0
    if job.state == JobStateEnum.Running:
        percent = 50  # Default to 50% for running jobs
    elif job.state == JobStateEnum.Finished:
        percent = 100

    # Determine exec and params based on job type
    exec_name = job.__class__.__name__
    params: Dict[str, str] = {}  # I guess it's unused in a response

    # Create log URL if available
    # log_url = None
    # for handler in job.logger.handlers:
    #     if hasattr(handler, "baseFilename"):
    #         log_url = f"file://{handler.baseFilename}"
    #         break

    # Create and return the TaskRsp model
    return TaskRsp(
        id=str(job.job_id),
        exec=exec_name,  # TODO: Is it really used?
        params=params,  # TODO: Is it really used?
        percent=percent,
        status=status_map.get(job.state, "PENDING"),
        log=job.last_log_line,
        createdAt=job.created_at,
        updatedAt=job.updated_at,
    )
