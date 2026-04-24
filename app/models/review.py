"""Data models for review persistence and API payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class ReviewBase(SQLModel):
    """Base attributes shared by review models."""

    customer_name: str = Field(
        min_length=1,
        max_length=255,
        description="Customer name that authored the review.",
    )
    review_date: datetime = Field(
        description="Date and time when the review was created.",
        index=True,
    )
    review_text: str = Field(min_length=1, description="Raw review text content.")


class Review(ReviewBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    classification: str = Field(
        min_length=1,
        description="Categorization for review sentiment.",
        index=True,
    )


class ReviewCreate(ReviewBase):
    """Payload model used to create a new review record."""


class ReviewRead(ReviewBase):
    """Response model for a single persisted review."""

    id: int
    classification: str = Field(
        min_length=1,
        description="Categorization for review sentiment.",
    )


class ReviewReportItem(SQLModel):
    """Aggregated quantity grouped by review classification."""

    classification: str
    total: int


class ReviewReport(SQLModel):
    """Response model for report endpoint aggregation."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_reviews: int
    by_classification: list[ReviewReportItem]


class ErrorResponse(BaseModel):
    """Response model for error responses."""

    detail: str
