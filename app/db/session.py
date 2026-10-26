from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


# Get the database engine
@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


# Get the session maker
@lru_cache
def get_sessionMaker() -> sessionmaker:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


# Get a database session
def get_db() -> Iterator[Session]:
    """(Generator + Context Manager)"""
    with get_sessionMaker()() as session:
        yield session
