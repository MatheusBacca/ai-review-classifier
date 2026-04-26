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

    @staticmethod
    def _apply_classification_filter(statement, classification: Optional[str]):
        """Filter by ``Review.classification`` when a value is provided."""
        if classification is not None:
            statement = statement.where(Review.classification == classification)
        return statement

    @staticmethod
    def _has_period_filter(
        start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> bool:
        return start_date is not None or end_date is not None

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
        classification: Optional[str] = None,
        *,
        page: int = 1,
        limit: int = 50,
    ) -> list[Review]:
        """Return a page of reviews with read-order rules.

        Without date filters, rows are ordered by ``id`` ascending. When
        ``start_date`` and/or ``end_date`` is set, order is ``review_date`` then
        ``id`` (both ascending).

        Args:
            start_date: Optional inclusive lower datetime bound.
            end_date: Optional inclusive upper datetime bound.
            classification: Optional exact match on ``Review.classification``.
            page: 1-based page index.
            limit: Page size (50–200 in API layer).

        Returns:
            List of matching reviews in the configured order.
        """
        offset = (page - 1) * limit
        statement = select(Review)
        statement = self._apply_period_filters(statement, start_date, end_date)
        statement = self._apply_classification_filter(statement, classification)
        if self._has_period_filter(start_date, end_date):
            statement = statement.order_by(Review.review_date.asc(), Review.id.asc())
        else:
            statement = statement.order_by(Review.id.asc())
        statement = statement.offset(offset).limit(limit)
        return list(self.session.exec(statement).all())

    def count_reviews(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        classification: Optional[str] = None,
    ) -> int:
        """Return how many reviews match the optional period (no ordering).

        Args:
            start_date: Optional inclusive lower datetime bound.
            end_date: Optional inclusive upper datetime bound.
            classification: Optional exact match on ``Review.classification``.

        Returns:
            Count of rows matching the filters.
        """
        statement = self._apply_period_filters(
            select(func.count(col(Review.id))),
            start_date,
            end_date,
        )
        statement = self._apply_classification_filter(statement, classification)
        return int(self.session.exec(statement).one())

    def get_by_id(
        self,
        review_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        classification: Optional[str] = None,
    ) -> Optional[Review]:
        """Return one review by identifier and optional period.

        Args:
            review_id: Numeric identifier of desired review.
            start_date: Optional inclusive lower datetime bound.
            end_date: Optional inclusive upper datetime bound.
            classification: Optional exact match on ``Review.classification``.

        Returns:
            Matching ``Review`` when found, otherwise ``None``.
        """
        statement = select(Review).where(Review.id == review_id)
        statement = self._apply_period_filters(statement, start_date, end_date)
        statement = self._apply_classification_filter(statement, classification)
        return self.session.exec(statement).first()

    def get_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        classification: Optional[str] = None,
    ) -> tuple[int, list[tuple[str, int]]]:
        """Return total and grouped counts by review classification.

        Groups with no date filter are ordered by ``MIN(id)`` per classification;
        with a date filter, by ``MIN(review_date)`` and then ``classification``.

        Args:
            start_date: Optional inclusive lower datetime bound.
            end_date: Optional inclusive upper datetime bound.
            classification: When set, only reviews with this classification are
                included; ``by_classification`` may contain a single group.

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
        total_statement = self._apply_classification_filter(
            total_statement, classification
        )
        total_reviews = int(self.session.exec(total_statement).one())

        has_period = self._has_period_filter(start_date, end_date)
        grouped_statement = self._apply_period_filters(
            select(Review.classification, func.count(col(Review.id))).group_by(
                Review.classification
            ),
            start_date,
            end_date,
        )
        grouped_statement = self._apply_classification_filter(
            grouped_statement, classification
        )
        if has_period:
            grouped_statement = grouped_statement.order_by(
                func.min(Review.review_date), Review.classification
            )
        else:
            grouped_statement = grouped_statement.order_by(
                func.min(Review.id), Review.classification
            )
        grouped_data = [
            (classification, int(total))
            for classification, total in self.session.exec(grouped_statement).all()
        ]
        return total_reviews, grouped_data
