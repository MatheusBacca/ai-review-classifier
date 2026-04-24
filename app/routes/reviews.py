"""Review API routes organized as a dedicated FastAPI router."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.database import get_session
from app.database.review import ReviewRepository
from app.models import ReviewCreate, ReviewRead, ReviewReport
from app.models.review import ErrorResponse
from app.service.review import ReviewNotFoundError, ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


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


def get_review_service(
    session: Annotated[Session, Depends(get_session)],
) -> ReviewService:
    """Create a review service instance bound to the request session."""
    repository = ReviewRepository(session)
    return ReviewService(repository)


@router.post(
    "",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review",
)
def create_review(
    payload: ReviewCreate,
    review_service: Annotated[ReviewService, Depends(get_review_service)],
) -> ReviewRead:
    """Create a new review using service-level business rules."""
    return review_service.create_review(payload)


@router.get("", response_model=list[ReviewRead], summary="List reviews")
def list_reviews(
    review_service: Annotated[ReviewService, Depends(get_review_service)],
    period: Annotated[
        tuple[Optional[datetime], Optional[datetime]], Depends(validate_date_range)
    ],
) -> list[ReviewRead]:
    """Return all reviews filtered by optional date period."""
    start_date, end_date = period
    return review_service.list_reviews(start_date, end_date)


@router.get("/report", response_model=ReviewReport, summary="Reviews report")
def reviews_report(
    review_service: Annotated[ReviewService, Depends(get_review_service)],
    period: Annotated[
        tuple[Optional[datetime], Optional[datetime]], Depends(validate_date_range)
    ],
) -> ReviewReport:
    """Return aggregated review counts by classification in the selected period."""
    start_date, end_date = period
    return review_service.get_reviews_report(start_date, end_date)


@router.get(
    "/{review_id}", response_model=ReviewRead, summary="Get review by id", responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Review not found",
                    }
                }
            },
        }
    }
)
def get_review_by_id(
    review_id: int,
    review_service: Annotated[ReviewService, Depends(get_review_service)],
    period: Annotated[
        tuple[Optional[datetime], Optional[datetime]], Depends(validate_date_range)
    ],
) -> ReviewRead:
    """Return a single review by identifier, respecting optional period filters."""
    start_date, end_date = period
    try:
        return review_service.get_review_by_id(review_id, start_date, end_date)
    except ReviewNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
