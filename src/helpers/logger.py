import logging
import sys
from logging import Logger
from pathlib import Path

from config_rdr import config

# Create a logs directory inside WORKING_DIR if it doesn't exist
logs_dir = Path(config.WORKING_DIR) / "logs"
logs_dir.mkdir(exist_ok=True, parents=True)


class NullLogger(Logger):
    """
    A logger that does nothing with log records.

    This is useful when you want to disable logging in certain parts of the application.
    """

    def __init__(self):
        super().__init__("nullLogger")
        self.addHandler(logging.NullHandler())


# Configure the root logger
def setup_logger():
    """
    Configure the root logger for the application.

    This sets up a logger that outputs to both console and a file.
    """
    # Create logger
    logger = logging.getLogger("zooprocess")
    logger.setLevel(logging.INFO)

    # Create formatters
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Create file handler
    file_handler = logging.FileHandler(logs_dir / "zooprocess.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Create and configure the logger
logger = setup_logger()
