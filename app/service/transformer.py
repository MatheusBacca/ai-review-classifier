"""Review text classification service powered by Hugging Face transformers."""

from transformers import pipeline

from app.config import settings
from app.utils.enums import ReviewClassification


class ReviewClassifier:
    """Classify review text into normalized sentiment labels."""

    def __init__(self) -> None:
        self._classifier = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            token=settings.huggingface_token if settings.huggingface_token else None,
        )

    def classify(self, review_text: str) -> ReviewClassification:
        rate = self._classifier(review_text)[0]
        stars = int(rate["label"][0])

        if stars <= 2:
            return ReviewClassification.negativa
        if stars == 3:
            return ReviewClassification.neutra
        return ReviewClassification.positiva


review_classifier = ReviewClassifier()
