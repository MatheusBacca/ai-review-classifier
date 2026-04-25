"""FastAPI entrypoint and app factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_and_tables
from app.routes.reviews import router as reviews_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Handle startup and shutdown events for application lifecycle.

    Args:
        _: FastAPI application instance (unused in this implementation).

    Yields:
        None.

    Example:
        >>> # Lifespan is executed automatically by FastAPI/Uvicorn.
        >>> True
        True
    """
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.

    Returns:
        Configured ``FastAPI`` app with router registration and lifespan.

    Example:
        >>> app = create_app()
        >>> app.title
        'AI Review Classifier API'
    """
    application = FastAPI(
        title="AI Review Classifier API",
        version="1.0.0",
        description="API for storing and reporting customer review classifications.",
        lifespan=lifespan,
    )
    application.include_router(reviews_router)
    return application


app = create_app()
