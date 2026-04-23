"""Data models for review persistence and API payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.utils.enums import ReviewClassification


class ReviewBase(SQLModel):
    """Base attributes shared by review models."""

    customer_name: str = Field(
        min_length=1,
        max_length=255,
        description="Customer name that authored the review.",
    )
    review_date: datetime = Field(
        description="Date and time when the review was created."
    )
    review_text: str = Field(min_length=1, description="Raw review text content.")
    classification: ReviewClassification = Field(
        description="Categorization for review sentiment."
    )


class ReviewCreate(ReviewBase):
    """Payload model used to create a new review record."""


class Review(ReviewBase, table=True):
    """SQLModel table that stores customer reviews."""

    id: Optional[int] = Field(default=None, primary_key=True)


class ReviewRead(ReviewBase):
    """Response model for a single persisted review."""

    id: int


class ReviewReportItem(SQLModel):
    """Aggregated quantity grouped by review classification."""

    classification: ReviewClassification
    total: int


class ReviewReport(SQLModel):
    """Response model for report endpoint aggregation."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_reviews: int
    by_classification: list[ReviewReportItem]
