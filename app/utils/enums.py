"""Domain enumerations used by the application."""

from enum import Enum


class ReviewClassification(str, Enum):
    """Allowed values for the review classification field."""

    positiva = "positiva"
    neutra = "neutra"
    negativa = "negativa"
