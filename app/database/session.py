"""Database setup and session management for SQLModel."""

from typing import Generator

from sqlmodel import Session, create_engine

from app.config import settings

engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)


def get_session() -> Generator[Session, None, None]:
    """Yield transactional SQLModel session for request handlers.

    Yields:
        Active SQLModel ``Session``.

    Example:
        >>> # with next(get_session()) as session: ...
        >>> True
        True
    """
    with Session(engine) as session:
        yield session
