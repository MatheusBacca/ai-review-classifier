"""Review API routes organized as a dedicated FastAPI router."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, func, select

from app.database import get_session
from app.models import Review, ReviewCreate, ReviewRead, ReviewReport, ReviewReportItem

router = APIRouter(tags=["reviews"])


def validate_date_range(
    start_date: Annotated[
        Optional[datetime],
        Query(description="Initial datetime for filtering reviews."),
    ] = None,
    end_date: Annotated[
        Optional[datetime],
        Query(description="Final datetime for filtering reviews."),
    ] = None,
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Validate that start date is not greater than end date."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be less than or equal to end_date.",
        )
    return start_date, end_date


def apply_period_filters(
    statement,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
):
    """Apply optional date range constraints to a SQLModel select statement."""
    if start_date:
        statement = statement.where(Review.review_date >= start_date)
    if end_date:
        statement = statement.where(Review.review_date <= end_date)
    return statement


@router.post(
    "/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review",
)
def create_review(
    payload: ReviewCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ReviewRead:
    """Persist a new review record and return it."""
    review: Review = Review.model_validate(payload)
    session.add(review)
    session.commit()
    session.refresh(review)
    return ReviewRead.model_validate(review)


@router.get("/reviews", response_model=list[ReviewRead], summary="List reviews")
def list_reviews(
    session: Annotated[Session, Depends(get_session)],
    period: Annotated[
        tuple[Optional[datetime], Optional[datetime]], Depends(validate_date_range)
    ],
) -> list[ReviewRead]:
    """Return all reviews filtered by optional date period."""
    start_date, end_date = period
    statement = select(Review).order_by(Review.review_date.desc())
    statement = apply_period_filters(statement, start_date, end_date)
    records: list[Review] = list(session.exec(statement).all())
    return [ReviewRead.model_validate(record) for record in records]


@router.get("/reviews/report", response_model=ReviewReport, summary="Reviews report")
def reviews_report(
    session: Annotated[Session, Depends(get_session)],
    period: Annotated[
        tuple[Optional[datetime], Optional[datetime]], Depends(validate_date_range)
    ],
) -> ReviewReport:
    """Return aggregated review counts by classification in the selected period."""
    start_date, end_date = period

    total_query = apply_period_filters(
        select(func.count(col(Review.id))), start_date, end_date
    )
    total_reviews: int = int(session.exec(total_query).one())

    grouped_query = apply_period_filters(
        select(Review.classification, func.count(col(Review.id))).group_by(
            Review.classification
        ),
        start_date,
        end_date,
    )
    grouped_data = session.exec(grouped_query).all()
    by_classification = [
        ReviewReportItem(classification=item[0], total=int(item[1]))
        for item in grouped_data
    ]

    return ReviewReport(
        start_date=start_date,
        end_date=end_date,
        total_reviews=total_reviews,
        by_classification=by_classification,
    )


@router.get(
    "/reviews/{review_id}", response_model=ReviewRead, summary="Get review by id"
)
def get_review_by_id(
    review_id: int,
    session: Annotated[Session, Depends(get_session)],
    period: Annotated[
        tuple[Optional[datetime], Optional[datetime]], Depends(validate_date_range)
    ],
) -> ReviewRead:
    """Return a single review by identifier, respecting optional period filters."""
    start_date, end_date = period
    statement = select(Review).where(Review.id == review_id)
    statement = apply_period_filters(statement, start_date, end_date)
    review = session.exec(statement).first()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found for given id and date filters.",
        )

    return ReviewRead.model_validate(review)
