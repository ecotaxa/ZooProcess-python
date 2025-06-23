from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional


def directory_date_range(
    path: Path,
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Determine the date range (earliest and latest modification dates) of all files in a given directory.

    This implementation uses a single pass through the files, updating min/max dates as it goes,
    which is more memory-efficient and faster for large directories than collecting all dates first.

    Args:
        path: Path to the directory to analyze

    Returns:
        A tuple containing (earliest_date, latest_date) as datetime objects.
        If the directory is empty or doesn't exist, returns (None, None).
    """
    if not path.exists() or not path.is_dir():
        return None, None

    earliest_date = None
    latest_date = None

    # Single pass through files, updating min/max as we go
    for f in path.iterdir():
        if not f.is_file():
            continue
        mod_time = datetime.fromtimestamp(f.stat().st_mtime)
        if earliest_date is None or mod_time < earliest_date:
            earliest_date = mod_time
        if latest_date is None or mod_time > latest_date:
            latest_date = mod_time

    return earliest_date, latest_date


def file_date(file_path: Path) -> datetime:
    return datetime.fromtimestamp(file_path.stat().st_mtime)
