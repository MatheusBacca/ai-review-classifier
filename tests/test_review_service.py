"""Pytest suite for review workflows with in-memory DB and API filters."""

from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.database.review import ReviewRepository
from app.models import Review, ReviewCreate
from app.service.review import ReviewService
from app.utils.enums import ReviewClassification
from tests.conftest import FakeReviewClassifier


def _patch_classifier(monkeypatch, fake_classifier: FakeReviewClassifier) -> None:
    monkeypatch.setattr(
        "app.service.review.get_review_classifier",
        lambda: fake_classifier,
    )


def _create_review_payload(review: dict[str, str]) -> dict[str, str]:
    return {
        "customer_name": review["customer_name"],
        "review_date": review["review_date"],
        "review_text": review["review_text"],
    }


def test_service_create_review_persists_data(
    session: Session,
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    repository = ReviewRepository(session)
    service = ReviewService(repository)
    payload = ReviewCreate(
        customer_name="Teste",
        review_date=datetime.fromisoformat("2026-04-25T09:00:00"),
        review_text="Produto excelente e entrega rapida.",
    )

    created = service.create_review(payload)

    assert created.id is not None
    assert created.classification == ReviewClassification.positiva

    saved = session.get(Review, created.id)
    assert saved is not None
    assert saved.classification == ReviewClassification.positiva
    assert saved.customer_name == "Teste"


def test_api_list_reviews_with_date_filters(
    client: TestClient,
    seed_reviews: list[dict[str, str]],
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    for review in seed_reviews:
        response = client.post("/reviews", json=_create_review_payload(review))
        assert response.status_code == 201

    target_date = seed_reviews[1]["review_date"][:10]
    expected_count = sum(
        1 for review in seed_reviews if review["review_date"][:10] == target_date
    )
    response = client.get(
        "/reviews",
        params={
            "start_date": f"{target_date}T00:00:00",
            "end_date": f"{target_date}T23:59:59",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == expected_count


def test_api_report_groups_by_classification(
    client: TestClient,
    seed_reviews: list[dict[str, str]],
    fake_classifier: FakeReviewClassifier,
    monkeypatch,
) -> None:
    _patch_classifier(monkeypatch, fake_classifier)
    for review in seed_reviews:
        response = client.post("/reviews", json=_create_review_payload(review))
        assert response.status_code == 201

    date_values = [datetime.fromisoformat(review["review_date"]) for review in seed_reviews]
    start_date = min(date_values).strftime("%Y-%m-%dT00:00:00")
    end_date = max(date_values).strftime("%Y-%m-%dT23:59:59")
    response = client.get(
        "/reviews/report",
        params={
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    assert response.status_code == 200
    report = response.json()
    assert report["total_reviews"] == len(seed_reviews)

    grouped = {item["classification"]: item["total"] for item in report["by_classification"]}
    expected_grouped = {
        ReviewClassification.positiva.value: 0,
        ReviewClassification.neutra.value: 0,
        ReviewClassification.negativa.value: 0,
    }
    for review in seed_reviews:
        expected_grouped[fake_classifier.classify(review["review_text"])] += 1

    assert grouped.get(ReviewClassification.positiva.value, 0) == expected_grouped[
        ReviewClassification.positiva.value
    ]
    assert grouped.get(ReviewClassification.neutra.value, 0) == expected_grouped[
        ReviewClassification.neutra.value
    ]
    assert grouped.get(ReviewClassification.negativa.value, 0) == expected_grouped[
        ReviewClassification.negativa.value
    ]
