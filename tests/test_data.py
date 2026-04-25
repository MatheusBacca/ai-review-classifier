"""Shared test data for review service and API tests.

Update `USER_DEFINED_REVIEWS` to quickly customize scenarios.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path


USER_DEFINED_REVIEWS = [
    {
        "customer_name": "Ana",
        "review_date": "2026-04-20T10:00:00",
        "review_text": "Produto excelente e entrega rapida.",
        "classification": "positiva",
    },
    {
        "customer_name": "Bruno",
        "review_date": "2026-04-21T11:00:00",
        "review_text": "Atende, mas poderia ser melhor.",
        "classification": "neutra",
    },
    {
        "customer_name": "Carla",
        "review_date": "2026-04-22T12:00:00",
        "review_text": "Nao gostei, veio com defeito.",
        "classification": "negativa",
    },
]

_TEST_DATA_FILE_CANDIDATES = (
    Path(__file__).with_name("test_data.json"),
)


def get_seed_reviews() -> list[dict[str, str]]:
    """Load external JSON test data when available, otherwise fallback defaults."""
    for file_path in _TEST_DATA_FILE_CANDIDATES:
        if file_path.exists():
            with file_path.open("r", encoding="utf-8") as json_file:
                loaded_reviews = json.load(json_file)
            return deepcopy(loaded_reviews)

    return deepcopy(USER_DEFINED_REVIEWS)
