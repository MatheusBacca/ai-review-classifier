"""Domain enumerations used by the application."""

from enum import Enum


class ReviewClassification(str, Enum):
    """Allowed values for the review classification field."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
