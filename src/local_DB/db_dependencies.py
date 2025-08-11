from .models import get_session_maker
from .sqlite_db import SQLAlchemyDB

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
            try:
                db.session.close()
            except Exception as e:
                # Ignore errors when closing the session
                # This prevents issues during teardown
                pass
