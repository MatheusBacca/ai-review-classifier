"""Shared pytest fixtures for review service tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.routes.reviews import router as reviews_router
from tests.test_data import get_seed_reviews


class FakeReviewClassifier:
    """Deterministic classifier used to isolate tests from transformers."""

    def classify(self, review_text: str) -> str:
        text = review_text.lower()
        if "excelente" in text or "rapida" in text:
            return "positiva"
        if "defeito" in text or "nao gostei" in text:
            return "negativa"
        return "neutra"


@pytest.fixture
def seed_reviews() -> list[dict[str, str]]:
    """Provide mutable seed data loaded from JSON/default source."""
    return get_seed_reviews()


@pytest.fixture
def fake_classifier() -> FakeReviewClassifier:
    """Provide a deterministic classifier mock."""
    return FakeReviewClassifier()


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """Provide an isolated in-memory SQLModel session per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    """Provide FastAPI test client wired to fixture session."""
    app = FastAPI()
    app.include_router(reviews_router)

    def override_get_session() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
