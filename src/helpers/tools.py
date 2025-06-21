import os
import sys
import time
from functools import wraps
from pathlib import Path

from logger import logger


def nameit(func):
    @wraps(func)
    def nameit_wrapper(*args, **kwargs):
        logger.info(f"Running: {func.__name__}")
        result = func(*args, **kwargs)
        return result

    return nameit_wrapper


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        # first item in the args, ie `args[0]` is `self`
        logger.info(
            f"Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds"
        )
        return result

    return timeit_wrapper


def eprint(*args, **kwargs):
    # Print to stderr for backward compatibility
    print(*args, file=sys.stderr, **kwargs)
    # Also log as error
    logger.error(" ".join(str(arg) for arg in args))


def create_folder(path: Path):
    logger.info(f"create folder: {path.as_posix()}")
    try:
        if not path.is_dir():
            # os.mkdir(path)
            # os.makedirs(path, exist_ok=True)
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"folder created: {path.absolute()}")
    except OSError as error:
        path_str = str(path.absolute())

        logger.error(f"cannot create folder: {path_str}, {str(error)}")
        eprint("cannot create folder: ", path_str, ", ", str(error))


def is_file_exist(path):
    return os.path.exists(path)
