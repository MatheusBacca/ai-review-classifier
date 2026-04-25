"""Domain enumerations used by the application."""

from enum import Enum


class ReviewClassification(str, Enum):
    """Allowed values for the review classification field.

    Attributes:
        positiva: Positive sentiment.
        neutra: Neutral sentiment.
        negativa: Negative sentiment.

    Example:
        >>> ReviewClassification.positiva.value
        'positiva'
    """

    positiva = "positiva"
    neutra = "neutra"
    negativa = "negativa"
