"""Review text classification service powered by Hugging Face transformers."""

from functools import lru_cache
from typing import Any, Callable, Optional

from app.config import settings
from app.utils.enums import ReviewClassification


class ReviewClassifier:
    """Classify review text into normalized sentiment labels.

    Example:
        >>> classifier = ReviewClassifier(classifier=lambda _text: [{"label": "5 stars"}])
        >>> classifier.classify("Excelente")
        <ReviewClassification.positiva: 'positiva'>
    """

    def __init__(
        self, classifier: Optional[Callable[[str], list[dict[str, Any]]]] = None
    ) -> None:
        """Create a sentiment classifier.

        Args:
            classifier: Optional callable used in tests to bypass model loading.

        Returns:
            None.
        """
        if classifier:
            self._classifier = classifier
            return

        from transformers import pipeline

        self._classifier = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            token=settings.huggingface_token if settings.huggingface_token else None,
        )

    def classify(self, review_text: str) -> ReviewClassification:
        """Classify review text based on model star labels.

        Args:
            review_text: Raw review text to classify.

        Returns:
            Sentiment classification represented by ``ReviewClassification``.

        Raises:
            KeyError: If model output misses expected ``label`` key.
            ValueError: If label does not start with a numeric star value.
        """
        rate = self._classifier(review_text)[0]
        stars = int(rate["label"][0])

        if stars <= 2:
            return ReviewClassification.negativa
        if stars == 3:
            return ReviewClassification.neutra
        return ReviewClassification.positiva


@lru_cache
def get_review_classifier() -> ReviewClassifier:
    """Return a cached classifier instance to avoid repeated model loads.

    Returns:
        Singleton-like ``ReviewClassifier`` for application runtime.

    Example:
        >>> isinstance(get_review_classifier(), ReviewClassifier)
        True
    """
    return ReviewClassifier()
