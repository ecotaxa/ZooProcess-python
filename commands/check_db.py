import os
from src.config_rdr import config
from src.local_db.sqlite_db import db_path
from src.logger import logger

# Check if the database file exists
db_file_path = db_path
if os.path.exists(db_file_path):
    logger.info(f"Database file exists at: {db_file_path}")
    logger.info(f"File size: {os.path.getsize(db_file_path)} bytes")
else:
    logger.error(f"Database file does not exist at: {db_file_path}")

# Print the WORKING_DIR for reference
logger.info(f"WORKING_DIR: {config.WORKING_DIR}")
