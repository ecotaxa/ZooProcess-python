import os
from typing import Optional

from sqlalchemy import Integer, String, create_engine, JSON
from sqlalchemy.orm import DeclarativeBase, sessionmaker, mapped_column, Mapped

from config_rdr import config


class Base(DeclarativeBase):
    pass


# Define the Example model based on the existing example table
class Example(Base):
    """
    SQLAlchemy model for the example table.
    """

    __tablename__ = "example"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String, nullable=False)
    value = mapped_column(String)

    def __repr__(self):
        return f"<Example(id={self.id}, name='{self.name}', value='{self.value}')>"


# Define the User model
class User(Base):
    """
    SQLAlchemy model for the user table.
    """

    __tablename__ = "user"

    id = mapped_column(String, primary_key=True)
    name = mapped_column(String, nullable=False)
    email = mapped_column(String, nullable=False, unique=True)
    password = mapped_column(String, nullable=False)  # Store encrypted password

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

    drive_name = mapped_column(String, primary_key=True, nullable=False)
    project_name = mapped_column(String, primary_key=True, nullable=False)
    scan_id = mapped_column(String, primary_key=True, nullable=False)
    scan_data = mapped_column(JSON, nullable=False)
    background_id: Mapped[Optional[str]]

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
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        # SQLite specific settings for better concurrency
        connect_args={"check_same_thread": False},
    )
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
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session(engine=None):
    """
    Create a SQLAlchemy session using the new SQLAlchemy v2 API.

    Args:
        engine (sqlalchemy.engine.Engine, optional): The SQLAlchemy engine.
            If None, a new engine will be created. Defaults to None.

    Returns:
        sqlalchemy.orm.Session: A SQLAlchemy session.
    """
    if engine is None:
        engine = get_engine()
    session_maker = sessionmaker(bind=engine)
    return session_maker()


def init_db():
    """
    Initialize the SQLite database with SQLAlchemy.

    Returns:
        str: The path to the SQLite database file.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)
    return os.path.join(config.WORKING_DIR, config.DB_NAME)
