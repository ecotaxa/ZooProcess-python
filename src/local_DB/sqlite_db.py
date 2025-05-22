import os
import sqlite3
from config_rdr import config
from .models import (
    get_engine,
    get_session_maker,
    init_db as sqlalchemy_init_db,
)


class SQLiteDB:
    """
    A class to interact with a SQLite database.

    This class provides backward compatibility with the old SQLite interface
    while using SQLAlchemy under the hood.

    Attributes:
        db_path (str): The full path to the SQLite database file.
        connection (sqlite3.Connection): The SQLite database connection.
    """

    def __init__(self, db_name=None):
        """
        Initialize the SQLite database.

        Args:
            db_name (str, optional): The name of the SQLite database file.
                If None, uses the DB_NAME from config. Defaults to None.
        """
        if db_name is None:
            db_name = config.DB_NAME
        self.db_path = os.path.join(config.WORKING_DIR, db_name)
        self.connection = None
        self.engine = get_engine(db_name)
        self.SessionMaker = get_session_maker(self.engine)
        self.session = None

    def connect(self):
        """
        Connect to the SQLite database.

        Returns:
            sqlite3.Connection: The SQLite database connection.
        """
        self.connection = sqlite3.connect(self.db_path)
        self.session = self.SessionMaker()
        return self.connection

    def close(self):
        """
        Close the SQLite database connection.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
        if self.session:
            self.session.close()
            self.session = None

    def __enter__(self):
        """
        Context manager entry point.

        Returns:
            SQLiteDB: The SQLiteDB instance.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.
        """
        self.close()

    def execute(self, query, params=None):
        """
        Execute a SQL query.

        This method provides backward compatibility with the old SQLite interface.
        For new code, it's recommended to use the SQLAlchemy ORM directly.

        Args:
            query (str): The SQL query to execute.
            params (tuple, optional): The parameters for the SQL query. Defaults to None.

        Returns:
            sqlite3.Cursor: The cursor object.
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        return cursor

    def commit(self):
        """
        Commit the current transaction.
        """
        if self.connection:
            self.connection.commit()
        if self.session:
            self.session.commit()

    def create_tables(self):
        """
        Create the database tables if they don't exist.
        """
        # Using SQLAlchemy to create tables
        from src.local_DB.models import Base

        Base.metadata.create_all(self.engine)


class SQLAlchemyDB:
    """
    A class to interact with a SQLite database using SQLAlchemy ORM.

    Attributes:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine.
        SessionMaker (sqlalchemy.orm.sessionmaker): The SQLAlchemy session maker.
        session (sqlalchemy.orm.Session): The SQLAlchemy session.
    """

    def __init__(self, db_name=None):
        """
        Initialize the SQLAlchemy database.

        Args:
            db_name (str, optional): The name of the SQLite database file.
                If None, uses the DB_NAME from config. Defaults to None.
        """
        if db_name is None:
            db_name = config.DB_NAME
        self.engine = get_engine(db_name)
        self.SessionMaker = get_session_maker(self.engine)
        self.session = None

    def __enter__(self):
        """
        Context manager entry point.

        Returns:
            SQLAlchemyDB: The SQLAlchemyDB instance.
        """
        self.session = self.SessionMaker()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.
        """
        if self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
            self.session = None


# Initialize the database when the module is imported
def init_db():
    """
    Initialize the SQLite database.

    Returns:
        str: The path to the SQLite database file.
    """
    return sqlalchemy_init_db()


# Create the database file if it doesn't exist
db_path = init_db()
