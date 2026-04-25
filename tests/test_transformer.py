"""Pytest suite for transformer sentiment normalization with mocked pipeline."""

from __future__ import annotations

from app.service.transformer import ReviewClassifier
from tests.test_data import get_seed_reviews


def test_classify_matches_expected_classification_from_seed_data() -> None:
    """Ensure mocked labels map to expected classification in test dataset."""
    reviews = get_seed_reviews()
    label_by_classification = {
        "negativa": "2 stars",
        "neutra": "3 stars",
        "positiva": "5 stars",
    }
    label_by_text = {
        review["review_text"]: label_by_classification[review["classification"]]
        for review in reviews
    }
    classifier = ReviewClassifier(classifier=lambda text: [{"label": label_by_text[text]}])

    for review in reviews:
        result = classifier.classify(review["review_text"])
        assert result == review["classification"]
