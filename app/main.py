"""FastAPI entrypoint and app factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_and_tables
from app.routes.reviews import router as reviews_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Handle startup and shutdown events for the application lifecycle."""
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    application = FastAPI(
        title="AI Review Classifier API",
        version="1.0.0",
        description="API for storing and reporting customer review classifications.",
        lifespan=lifespan,
    )
    application.include_router(reviews_router)
    return application


app = create_app()
