"""Data models for review persistence and API payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator
from sqlmodel import Field, SQLModel


class ReviewBase(SQLModel):
    """Base attributes shared by review models.

    Attributes:
        customer_name: Name of the customer that authored the review.
        review_date: Datetime when the review event happened.
        review_text: Free text content written by the customer.

    Example:
        >>> ReviewBase(
        ...     customer_name="Ana",
        ...     review_date=datetime.fromisoformat("2026-04-20T10:00:00"),
        ...     review_text="Produto excelente.",
        ... )
    """

    customer_name: str = Field(
        min_length=1,
        max_length=255,
        description="Customer name that authored the review.",
    )
    review_date: datetime = Field(
        description="Date and time when the review was created.",
        index=True,
    )
    review_text: str = Field(
        min_length=1,
        description="Raw review text content.",
        nullable=False,
    )

    @field_validator("customer_name", "review_text")
    @classmethod
    def validate_non_blank_text(cls, value: str) -> str:
        """Reject values that contain only whitespace.

        Args:
            value: Raw string received in request payload.

        Returns:
            The validated original string.

        Raises:
            ValueError: If the provided string is empty after trimming spaces.
        """
        if not value.strip():
            raise ValueError("must not be blank.")
        return value


class Review(ReviewBase, table=True):
    """SQLModel table mapping for persisted reviews.

    Attributes:
        id: Auto-generated numeric identifier.
        classification: Sentiment class calculated for the review.

    Example:
        >>> Review(
        ...     customer_name="Ana",
        ...     review_date=datetime.fromisoformat("2026-04-20T10:00:00"),
        ...     review_text="Produto excelente.",
        ...     classification="positiva",
        ... )
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    classification: str = Field(
        min_length=1,
        description="Categorization for review sentiment.",
        index=True,
    )


class ReviewCreate(ReviewBase):
    """Payload model used to create a new review record.

    Example:
        >>> ReviewCreate(
        ...     customer_name="Ana",
        ...     review_date=datetime.fromisoformat("2026-04-20T10:00:00"),
        ...     review_text="Produto excelente.",
        ... )
    """


class ReviewRead(ReviewBase):
    """Response model for a single persisted review.

    Attributes:
        id: Numeric review identifier.
        classification: Persisted sentiment class.

    Example:
        >>> ReviewRead(
        ...     id=1,
        ...     customer_name="Ana",
        ...     review_date=datetime.fromisoformat("2026-04-20T10:00:00"),
        ...     review_text="Produto excelente.",
        ...     classification="positiva",
        ... )
    """

    id: int
    classification: str = Field(
        min_length=1,
        description="Categorization for review sentiment.",
    )


class ReviewReportItem(SQLModel):
    """Aggregated quantity grouped by review classification.

    Attributes:
        classification: Sentiment class label.
        total: Number of rows in this class.
    """

    classification: str
    total: int


class ReviewReport(SQLModel):
    """Response model for report endpoint aggregation.

    Attributes:
        start_date: Initial datetime considered in report.
        end_date: Final datetime considered in report.
        total_reviews: Number of reviews in selected period.
        by_classification: Grouped counts by sentiment class.
    """

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_reviews: int
    by_classification: list[ReviewReportItem]


class ErrorResponse(BaseModel):
    """Response model for error responses.

    Attributes:
        detail: Human-readable error explanation.
    """

    detail: str
