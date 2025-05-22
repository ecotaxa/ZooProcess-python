import os
import importlib
from pathlib import Path
from collections import namedtuple
from dotenv import load_dotenv

# Get the environment (dev, prod, or None for testing)
env = os.environ.get("APP_ENV")
# Only load the .env file if APP_ENV is set
if env:
    if env in ["dev", "prod"]:
        load_dotenv(".env." + env)
    else:
        raise ValueError("Invalid APP_ENV value. Must be 'dev' or 'prod'.")

# Get the working directory from the environment variable or use the current directory
WORKING_DIR = os.environ.get("WORKING_DIR", os.getcwd())
# Get the database file name from the environment variable or use the default
DB_NAME = os.environ.get("DB_NAME", "v10.sqlite")
# Get the drive list from the environment variable or use an empty list
DRIVES = os.environ.get("DRIVES", "").split(",") if os.environ.get("DRIVES") else []
# Get the database server URL from the environment variable or use a default
DBSERVER = os.environ.get("DBSERVER", "http://zooprocess.imev-mer.fr:8081/v1")

# Create a named tuple for configuration
Config = namedtuple("Config", ["WORKING_DIR", "DB_NAME", "DRIVES", "dbserver"])

# Create the config instance with all required attributes
config = Config(
    WORKING_DIR=WORKING_DIR, DB_NAME=DB_NAME, DRIVES=DRIVES, dbserver=DBSERVER
)
