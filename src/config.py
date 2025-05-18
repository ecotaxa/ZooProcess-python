import os
import importlib
from pathlib import Path

env = os.environ.get("APP_ENV", "development")
# Get the working directory from environment variable or use the current directory
WORKING_DIR = os.environ.get("WORKING_DIR", os.getcwd())
# Get the database file name from environment variable or use the default
DB_NAME = os.environ.get("DB_NAME", "v10.sqlite")

# Import the environment-specific configuration
config = importlib.import_module(f"src.config_{env}")

# Add WORKING_DIR and DB_NAME to the config module
config.WORKING_DIR = WORKING_DIR
config.DB_NAME = DB_NAME
