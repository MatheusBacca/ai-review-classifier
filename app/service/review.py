"""Business rules layer for review workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.database.review import ReviewRepository
from app.models import Review, ReviewCreate, ReviewRead, ReviewReport, ReviewReportItem
from app.service.transformer import get_review_classifier


class ReviewNotFoundError(Exception):
    """Raised when a review cannot be found with the requested filters."""


class ReviewService:
    """Encapsulate business rules for review operations."""

    def __init__(self, review_repository: ReviewRepository) -> None:
        """Store the repository dependency used by this service."""
        self.review_repository = review_repository

    def create_review(self, payload: ReviewCreate) -> ReviewRead:
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
    ) -> list[ReviewRead]:
        """List all reviews filtered by an optional period."""
        reviews = self.review_repository.list_reviews(start_date, end_date)
        return [ReviewRead.model_validate(review) for review in reviews]

    def get_review_by_id(
        self,
        review_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ReviewRead:
        """Fetch one review by id or raise domain not found error."""
        review = self.review_repository.get_by_id(review_id, start_date, end_date)
        if review is None:
            raise ReviewNotFoundError("Review not found for given id and date filters.")
        return ReviewRead.model_validate(review)

    def get_reviews_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ReviewReport:
        """Build an aggregated report grouped by review classification."""
        total_reviews, grouped_data = self.review_repository.get_report(
            start_date,
            end_date,
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
