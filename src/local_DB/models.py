import os

from sqlalchemy import Column, Integer, String, create_engine, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from config_rdr import config

# Create a base class for SQLAlchemy models
Base = declarative_base()


# Define the Example model based on the existing example table
class Example(Base):
    """
    SQLAlchemy model for the example table.
    """

    __tablename__ = "example"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    value = Column(String)

    def __repr__(self):
        return f"<Example(id={self.id}, name='{self.name}', value='{self.value}')>"


# Define the User model
class User(Base):
    """
    SQLAlchemy model for the user table.
    """

    __tablename__ = "user"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)  # Store encrypted password

    def __repr__(self):
        return f"<User(id='{self.id}', name='{self.name}', email='{self.email}')>"


# Define the InFlightScan model
class InFlightScan(Base):
    """
    SQLAlchemy model for the in_flight_scans table.

    This table stores information about scans that are _going to_ be processed.
    Legacy app does not allow such pattern, so we need some extra storage.
    """

    __tablename__ = "in_flight_scans"

    drive_name = Column(String, primary_key=True, nullable=False)
    project_name = Column(String, primary_key=True, nullable=False)
    scan_id = Column(String, primary_key=True, nullable=False)
    scan_data = Column(JSON, nullable=False)

    def __repr__(self):
        return f"<InFlightScan(scan_id='{self.scan_id}', project_name='{self.project_name}', drive_name='{self.drive_name}')>"


# Database connection and session management
def get_engine(db_name=None):
    """
    Create a SQLAlchemy engine for the SQLite database.

    Args:
        db_name (str, optional): The name of the SQLite database file.
            If None, uses the DB_NAME from config. Defaults to None.

    Returns:
        sqlalchemy.engine.Engine: The SQLAlchemy engine.
    """
    if db_name is None:
        db_name = config.DB_NAME
    db_path = os.path.join(config.WORKING_DIR, db_name)
    engine = create_engine(f"sqlite:///{db_path}")
    return engine


def get_session_maker(engine=None):
    """
    Create a SQLAlchemy session maker.

    Args:
        engine (sqlalchemy.engine.Engine, optional): The SQLAlchemy engine.
            If None, a new engine will be created. Defaults to None.

    Returns:
        sqlalchemy.orm.sessionmaker: The SQLAlchemy session maker.
    """
    if engine is None:
        engine = get_engine()
    return sessionmaker(bind=engine)


def init_db():
    """
    Initialize the SQLite database with SQLAlchemy.

    Returns:
        str: The path to the SQLite database file.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)
    return os.path.join(config.WORKING_DIR, config.DB_NAME)
