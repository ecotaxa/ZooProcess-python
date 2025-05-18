from sqlalchemy.orm import Session
from fastapi import Depends

from src.db_models import get_session_maker
from src.sqlite_db import SQLAlchemyDB

# Create a session maker
SessionMaker = get_session_maker()


def get_db():
    """
    FastAPI dependency that provides a SQLAlchemy database session.

    The session is automatically closed when the request is finished.

    Yields:
        Session: A SQLAlchemy database session.
    """
    db = SQLAlchemyDB()
    db.session = SessionMaker()
    try:
        yield db.session
    finally:
        if db.session:
            db.session.close()
