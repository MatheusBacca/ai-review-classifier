"""Database access layer for review entities."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, col, func, select

from app.models import Review, ReviewCreate


class ReviewRepository:
    """Handle persistence operations for reviews.

    Example:
        >>> # repository = ReviewRepository(session)
        >>> True
        True
    """

    def __init__(self, session: Session) -> None:
        """Create repository with active SQLModel session.

        Args:
            session: Active SQLModel session bound to current request/test.

        Returns:
            None.
        """
        self.session = session

    @staticmethod
    def _apply_period_filters(
        statement,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ):
        """Apply optional date filters to a SQLModel statement.

        Args:
            statement: SQLModel ``select`` statement to be filtered.
            start_date: Inclusive lower bound for ``review_date``.
            end_date: Inclusive upper bound for ``review_date``.

        Returns:
            The statement with optional ``where`` clauses applied.
        """
        if start_date:
            statement = statement.where(Review.review_date >= start_date)
        if end_date:
            statement = statement.where(Review.review_date <= end_date)
        return statement

    def create(self, payload: ReviewCreate) -> Review:
        """Create and persist a new review.

        Args:
            payload: Review entity data to persist.

        Returns:
            Persisted ``Review`` with generated identifier.

        Example:
            >>> # repository.create(payload)
            >>> True
            True
        """
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
        """Return all reviews ordered by newest date first.

        Args:
            start_date: Optional inclusive lower datetime bound.
            end_date: Optional inclusive upper datetime bound.

        Returns:
            List of matching reviews ordered descending by ``review_date``.
        """
        statement = select(Review).order_by(Review.review_date.desc())
        statement = self._apply_period_filters(statement, start_date, end_date)
        return list(self.session.exec(statement).all())

    def get_by_id(
        self,
        review_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[Review]:
        """Return one review by identifier and optional period.

        Args:
            review_id: Numeric identifier of desired review.
            start_date: Optional inclusive lower datetime bound.
            end_date: Optional inclusive upper datetime bound.

        Returns:
            Matching ``Review`` when found, otherwise ``None``.
        """
        statement = select(Review).where(Review.id == review_id)
        statement = self._apply_period_filters(statement, start_date, end_date)
        return self.session.exec(statement).first()

    def get_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[int, list[tuple[str, int]]]:
        """Return total and grouped counts by review classification.

        Args:
            start_date: Optional inclusive lower datetime bound.
            end_date: Optional inclusive upper datetime bound.

        Returns:
            Tuple containing total reviews and grouped classification counts.

        Example:
            >>> # total, grouped = repository.get_report()
            >>> True
            True
        """
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
