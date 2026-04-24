"""Database access layer for review entities."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, col, func, select

from app.models import Review, ReviewCreate


class ReviewRepository:
    """Handle persistence operations for reviews."""

    def __init__(self, session: Session) -> None:
        """Store an active SQLModel session for repository operations."""
        self.session = session

    @staticmethod
    def _apply_period_filters(
        statement,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ):
        """Apply optional date filters to a SQLModel select statement."""
        if start_date:
            statement = statement.where(Review.review_date >= start_date)
        if end_date:
            statement = statement.where(Review.review_date <= end_date)
        return statement

    def create(self, payload: ReviewCreate) -> Review:
        """Create and persist a new review."""
        review = Review.model_validate(payload)
        self.session.add(review)
        self.session.commit()
        self.session.refresh(review)
        return review

    def list_reviews(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[Review]:
        """Return all reviews ordered by newest date first."""
        statement = select(Review).order_by(Review.review_date.desc())
        statement = self._apply_period_filters(statement, start_date, end_date)
        return list(self.session.exec(statement).all())

    def get_by_id(
        self,
        review_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[Review]:
        """Return one review by identifier and optional period."""
        statement = select(Review).where(Review.id == review_id)
        statement = self._apply_period_filters(statement, start_date, end_date)
        return self.session.exec(statement).first()

    def get_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[int, list[tuple[str, int]]]:
        """Return total and grouped counts by review classification."""
        total_statement = self._apply_period_filters(
            select(func.count(col(Review.id))),
            start_date,
            end_date,
        )
        total_reviews = int(self.session.exec(total_statement).one())

        grouped_statement = self._apply_period_filters(
            select(Review.classification, func.count(col(Review.id))).group_by(
                Review.classification
            ),
            start_date,
            end_date,
        )
        grouped_data = [
            (classification, int(total))
            for classification, total in self.session.exec(grouped_statement).all()
        ]
        return total_reviews, grouped_data
