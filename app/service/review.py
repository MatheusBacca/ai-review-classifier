"""Business rules layer for review workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.database.review import ReviewRepository
from app.models import (
    PaginationInfo,
    Review,
    ReviewCreate,
    ReviewListResponse,
    ReviewRead,
    ReviewReport,
    ReviewReportItem,
)
from app.service.transformer import get_review_classifier


class ReviewNotFoundError(Exception):
    """Raised when a review cannot be found with the requested filters.

    Example:
        >>> raise ReviewNotFoundError("Review not found")
    """


class ReviewService:
    """Encapsulate business rules for review operations.

    Example:
        >>> # service = ReviewService(repository)
        >>> True
        True
    """

    def __init__(self, review_repository: ReviewRepository) -> None:
        """Create a service with repository dependency.

        Args:
            review_repository: Persistence gateway for review entities.

        Returns:
            None.
        """
        self.review_repository = review_repository

    def create_review(self, payload: ReviewCreate) -> ReviewRead:
        """Create and persist a review with computed classification.

        Args:
            payload: Input data used to create a new review.

        Returns:
            Persisted review representation.

        Example:
            >>> # service.create_review(payload)
            >>> True
            True
        """
        classificacao = get_review_classifier().classify(payload.review_text)

        review_db = Review(
            **payload.model_dump(),
            classification=classificacao,
        )

        review = self.review_repository.create(review_db)

        return ReviewRead.model_validate(review)

    def list_reviews(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        *,
        classification: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> ReviewListResponse:
        """List reviews for one page, filtered by an optional period.

        Args:
            start_date: Optional start datetime for inclusive filtering.
            end_date: Optional end datetime for inclusive filtering.
            classification: Optional exact match on stored sentiment.
            page: 1-based page number.
            limit: Page size (caller enforces 50–200 in HTTP layer).

        Returns:
            Paged list with matching reviews and ``PaginationInfo``.

        Example:
            >>> # service.list_reviews()
            >>> True
            True
        """
        total = self.review_repository.count_reviews(
            start_date, end_date, classification
        )
        reviews = self.review_repository.list_reviews(
            start_date,
            end_date,
            classification,
            page=page,
            limit=limit,
        )
        items = [ReviewRead.model_validate(review) for review in reviews]
        if total == 0:
            last_page = 0
        else:
            last_page = (total + limit - 1) // limit
        return ReviewListResponse(
            items=items,
            pagination=PaginationInfo(
                page=page,
                itens=len(items),
                total=total,
                last_page=last_page,
            ),
        )

    def get_review_by_id(
        self,
        review_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        classification: Optional[str] = None,
    ) -> ReviewRead:
        """Fetch one review by id or raise domain not found error.

        Args:
            review_id: Numeric identifier of desired review.
            start_date: Optional start datetime for filtering.
            end_date: Optional end datetime for filtering.
            classification: Optional exact match on stored sentiment.

        Returns:
            Matching persisted review.

        Raises:
            ReviewNotFoundError: If no review matches id and period.

        Example:
            >>> # service.get_review_by_id(1)
            >>> True
            True
        """
        review = self.review_repository.get_by_id(
            review_id, start_date, end_date, classification
        )
        if review is None:
            raise ReviewNotFoundError(
                "Review not found for the given id and read filters (dates and/or classification)."
            )
        return ReviewRead.model_validate(review)

    def get_reviews_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        classification: Optional[str] = None,
    ) -> ReviewReport:
        """Build aggregated report grouped by review classification.

        Args:
            start_date: Optional start datetime for report interval.
            end_date: Optional end datetime for report interval.
            classification: When set, only that sentiment is included.

        Returns:
            Aggregated counts and total reviews for selected range.

        Example:
            >>> # service.get_reviews_report()
            >>> True
            True
        """
        total_reviews, grouped_data = self.review_repository.get_report(
            start_date,
            end_date,
            classification,
        )
        by_classification = [
            ReviewReportItem(classification=classification, total=total)
            for classification, total in grouped_data
        ]
        return ReviewReport(
            start_date=start_date,
            end_date=end_date,
            total_reviews=total_reviews,
            by_classification=by_classification,
        )
