from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    All SQLAlchemy models inherit from this.
    It keeps track of all table definitions
    so we can create them all at once.
    """
    pass