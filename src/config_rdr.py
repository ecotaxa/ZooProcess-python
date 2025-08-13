import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv, find_dotenv

# Get the environment (dev, prod, or None for testing)
env = os.environ.get("APP_ENV")
# Only load the .env file if APP_ENV is set
if env:
    if env not in ["dev", "prod"]:
        raise ValueError("Invalid APP_ENV value. Must be 'dev' or 'prod'.")
    env_file = find_dotenv(".env." + env, True)
    load_dotenv(env_file)
else:
    raise ValueError("APP_ENV not set.")

# Get the working directory from the environment variable or use the current directory
_WORKING_DIR = os.environ.get("WORKING_DIR", os.getcwd())
if not _WORKING_DIR.startswith("/"):
    # Consider a relative path is relative to the env file
    _WORKING_DIR = (Path(env_file).parent / _WORKING_DIR).as_posix()
    print("Working directory: " + _WORKING_DIR)
# Get the database file name from the environment variable or use the default
_DB_NAME = os.environ.get("DB_NAME", "v10.sqlite")
# Get the drive list from the environment variable or use an empty list
_DRIVES = os.environ.get("DRIVES", "").split(",") if os.environ.get("DRIVES") else []
# Get the database server URL from the environment variable or use a default
_DBSERVER = os.environ.get("DBSERVER", "http://zooprocess.imev-mer.fr:8081/v1")
# Get the public URL from the environment variable or use a default
_PUBLIC_URL = os.environ.get("PUBLIC_URL", "http://localhost:5000")
# Get the secret key for JWT token signing and verification
_SECRET_KEY = os.environ.get("SECRET")
assert _SECRET_KEY is not None, "SECRET_KEY not set"
# Get the separator server URL from the environment variable or use a default
_SEPARATOR_SERVER = os.environ.get("SEPARATOR_SERVER", "http://localhost:55000/")
# Get the classifier server URL from the environment variable or use a default
_CLASSIFIER_SERVER = os.environ.get("CLASSIFIER_SERVER", "http://localhost:55001/")
# Get the EcoTaxa server URL from the environment variable or use a default
_ECOTAXA_SERVER = os.environ.get("ECOTAXA_SERVER", "https://ecotaxa.obs-vlfr.fr/api")


# Configuration class
class Config:
    """Configuration class with typed members."""

    def __init__(
        self,
        WORKING_DIR: str,
        DB_NAME: str,
        DRIVES: List[str],
        dbserver: str,
        public_url: str,
        SECRET_KEY: str,
        SEPARATOR_SERVER: str,
        CLASSIFIER_SERVER: str,
        ECOTAXA_SERVER: str,
    ):
        """
        Initialize the Config class with typed members.

        Args:
            WORKING_DIR (str): The working directory path
            DB_NAME (str): The database name
            DRIVES (List[str]): A list of drive paths
            dbserver (str): The database server URL
            public_url (str): The public URL for the application
            SECRET_KEY (str): The secret key for JWT token signing and verification
            SEPARATOR_SERVER (str): The separator server URL
            CLASSIFIER_SERVER (str): The classifier server URL
            ECOTAXA_SERVER (str): The EcoTaxa server URL
        """
        self.WORKING_DIR: str = WORKING_DIR
        self.DB_NAME: str = DB_NAME
        self._DRIVES: List[Path] = [Path(a_drive) for a_drive in DRIVES]
        self.DB_SERVER: str = dbserver
        self.PUBLIC_URL: str = public_url
        self.SECRET_KEY: str = SECRET_KEY
        self.SEPARATOR_SERVER: str = SEPARATOR_SERVER
        self.CLASSIFIER_SERVER: str = CLASSIFIER_SERVER
        self.ECOTAXA_SERVER: str = ECOTAXA_SERVER

    def get_drives(self) -> List[Path]:
        return self._DRIVES


# Create the config instance with all required attributes
config = Config(
    WORKING_DIR=_WORKING_DIR,
    DB_NAME=_DB_NAME,
    DRIVES=_DRIVES,
    dbserver=_DBSERVER,
    public_url=_PUBLIC_URL,
    SECRET_KEY=_SECRET_KEY,
    SEPARATOR_SERVER=_SEPARATOR_SERVER,
    CLASSIFIER_SERVER=_CLASSIFIER_SERVER,
    ECOTAXA_SERVER=_ECOTAXA_SERVER,
)
