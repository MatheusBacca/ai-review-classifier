"""Database setup and session management for SQLModel."""

from typing import Generator

from sqlmodel import SQLModel, Session, create_engine

from app.config import settings

engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)


def create_db_and_tables() -> None:
    """Create all mapped SQLModel tables in the configured database."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Provide a transactional SQLModel session for request handlers."""
    with Session(engine) as session:
        yield session
