"""
Booking Service
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.booking import Booking
from app.models.centre import DiagnosticCentre, DiagnosticTest
from app.models.enums import BookingStatusEnum
from app.schemas.booking import BookingCreateRequest


def create_booking(db: Session, user_id: str, payload: BookingCreateRequest) -> Booking:
    """Create a new booking for the user."""
    # Validate Centre exists
    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == payload.centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Diagnostic centre not found")

    # Validate Test exists and belongs to the specified centre
    test = db.query(DiagnosticTest).filter(DiagnosticTest.id == payload.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Diagnostic test not found")
    
    if test.centre_id != centre.id:
        raise HTTPException(status_code=400, detail="This test is not offered at the selected centre")

    # Snapshot the price
    amount = test.price

    booking = Booking(
        user_id=user_id,
        test_id=test.id,
        centre_id=centre.id,
        appointment_datetime=payload.appointment_datetime,
        amount=amount,
        status=BookingStatusEnum.PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_user_bookings(db: Session, user_id: str) -> list[Booking]:
    """Retrieve all bookings for a specific user."""
    return db.query(Booking).filter(Booking.user_id == user_id).order_by(Booking.created_at.desc()).all()


def cancel_booking(db: Session, user_id: str, booking_id: str) -> Booking:
    """Cancel a PENDING booking for the user."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")

    if booking.status != BookingStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot cancel booking with status {booking.status.value}")

    booking.status = BookingStatusEnum.CANCELLED
    db.commit()
    db.refresh(booking)
    return booking
