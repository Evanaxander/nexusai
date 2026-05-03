from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import get_settings

settings = get_settings()

# Create the database engine
# pool_pre_ping=True: tests connection before using it
# prevents "connection closed" errors after idle time
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,        # max 5 persistent connections
    max_overflow=10,    # allow 10 extra connections under load
    echo=False          # set True to see SQL queries in terminal
)

# Session factory — creates new DB sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — injects a DB session into endpoints.
    Automatically closes the session when the request finishes,
    even if an error occurred.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()