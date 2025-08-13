import os

from config_rdr import config
from .models import get_engine, get_session_maker


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
            try:
                if exc_type:
                    self.session.rollback()
                else:
                    self.session.commit()
                self.session.close()
            except Exception as e:
                # Ignore errors when closing the session
                pass
            self.session = None
