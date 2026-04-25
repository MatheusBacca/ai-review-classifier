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
    """Validate that start date is not greater than end date.

    Args:
        start_date: Optional initial datetime from query params.
        end_date: Optional final datetime from query params.

    Returns:
        Tuple with normalized ``(start_date, end_date)`` values.

    Raises:
        HTTPException: If ``start_date`` is greater than ``end_date``.

    Example:
        >>> validate_date_range(
        ...     datetime.fromisoformat("2026-04-01T00:00:00"),
        ...     datetime.fromisoformat("2026-04-30T23:59:59"),
        ... )
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be less than or equal to end_date.",
        )
    return start_date, end_date


def get_review_service(
    session: Annotated[Session, Depends(get_session)],
) -> ReviewService:
    """Build a review service instance for current request.

    Args:
        session: Active SQLModel session resolved by dependency injection.

    Returns:
        A configured ``ReviewService``.

    Example:
        >>> # Used by FastAPI Depends(get_review_service)
        >>> isinstance(get_review_service.__name__, str)
        True
    """
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
    """Create a new review using service-level business rules.

    Args:
        payload: Incoming request payload with customer and review data.
        review_service: Domain service injected by FastAPI.

    Returns:
        Persisted review representation.

    Raises:
        HTTPException: Propagated from validation layer when payload is invalid.

    Example:
        >>> # POST /reviews
        >>> True
        True
    """
    return review_service.create_review(payload)


@router.get("", response_model=list[ReviewRead], summary="List reviews")
def list_reviews(
    review_service: Annotated[ReviewService, Depends(get_review_service)],
    period: Annotated[
        tuple[Optional[datetime], Optional[datetime]], Depends(validate_date_range)
    ],
) -> list[ReviewRead]:
    """Return all reviews filtered by optional date period.

    Args:
        review_service: Domain service injected by FastAPI.
        period: Tuple with ``(start_date, end_date)`` validated by dependency.

    Returns:
        A list of persisted reviews matching the optional period.

    Example:
        >>> # GET /reviews?start_date=...&end_date=...
        >>> True
        True
    """
    start_date, end_date = period
    return review_service.list_reviews(start_date, end_date)


@router.get("/report", response_model=ReviewReport, summary="Reviews report")
def reviews_report(
    review_service: Annotated[ReviewService, Depends(get_review_service)],
    period: Annotated[
        tuple[Optional[datetime], Optional[datetime]], Depends(validate_date_range)
    ],
) -> ReviewReport:
    """Return grouped review report for the selected period.

    Args:
        review_service: Domain service injected by FastAPI.
        period: Tuple with optional period bounds.

    Returns:
        Aggregated report grouped by classification.

    Example:
        >>> # GET /reviews/report
        >>> True
        True
    """
    start_date, end_date = period
    return review_service.get_reviews_report(start_date, end_date)


@router.get(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Get review by id",
    responses={
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
    },
)
def get_review_by_id(
    review_id: int,
    review_service: Annotated[ReviewService, Depends(get_review_service)],
    period: Annotated[
        tuple[Optional[datetime], Optional[datetime]], Depends(validate_date_range)
    ],
) -> ReviewRead:
    """Return one review by identifier and optional period.

    Args:
        review_id: Numeric review identifier from path.
        review_service: Domain service injected by FastAPI.
        period: Tuple with optional period bounds.

    Returns:
        Matching persisted review.

    Raises:
        HTTPException: If review cannot be found for given id/period.

    Example:
        >>> # GET /reviews/1
        >>> True
        True
    """
    start_date, end_date = period
    try:
        return review_service.get_review_by_id(review_id, start_date, end_date)
    except ReviewNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
