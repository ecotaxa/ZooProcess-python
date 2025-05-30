import os
from pathlib import Path
from typing import List

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
# Get the public URL from the environment variable or use a default
PUBLIC_URL = os.environ.get("PUBLIC_URL", "http://localhost:5000")
# Get the secret key for JWT token signing and verification
SECRET_KEY = os.environ.get("SECRET", "your-secret-key")


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
        """
        self.WORKING_DIR: str = WORKING_DIR
        self.DB_NAME: str = DB_NAME
        self.DRIVES: List[Path] = [Path(a_drive) for a_drive in DRIVES]
        self.dbserver: str = dbserver
        self.public_url: str = public_url
        self.SECRET_KEY: str = SECRET_KEY


# Create the config instance with all required attributes
config = Config(
    WORKING_DIR=WORKING_DIR,
    DB_NAME=DB_NAME,
    DRIVES=DRIVES,
    dbserver=DBSERVER,
    public_url=PUBLIC_URL,
    SECRET_KEY=SECRET_KEY,
)
