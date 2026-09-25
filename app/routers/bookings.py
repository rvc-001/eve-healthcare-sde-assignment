"""
Bookings Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.booking import BookingCreateRequest, BookingResponse
from app.services import booking_service
from app.utils.response import send_response

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", summary="Create a new booking", status_code=201)
def create_booking(
    payload: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Book a diagnostic test at a specific centre.
    The booking price is snapshotted at creation time, and the status starts as PENDING.
    """
    booking = booking_service.create_booking(db, current_user.id, payload)
    return send_response(
        success=True,
        message="Booking created successfully.",
        data=BookingResponse.model_validate(booking).model_dump()
    )


@router.get("/", summary="List my bookings")
def list_user_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all bookings belonging to the currently authenticated user."""
    bookings = booking_service.get_user_bookings(db, current_user.id)
    return send_response(
        success=True,
        message="Bookings retrieved successfully.",
        data=[BookingResponse.model_validate(b).model_dump() for b in bookings]
    )


@router.patch("/{booking_id}/cancel", summary="Cancel a booking")
def cancel_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a booking (only if it is still in PENDING state)."""
    booking = booking_service.cancel_booking(db, current_user.id, booking_id)
    return send_response(
        success=True,
        message="Booking cancelled successfully.",
        data=BookingResponse.model_validate(booking).model_dump()
    )
