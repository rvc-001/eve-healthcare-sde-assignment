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

    # Validate Slot
    from app.models.centre import TestSlot
    slot = db.query(TestSlot).filter(TestSlot.id == payload.slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Test slot not found")
    if slot.test_id != test.id:
        raise HTTPException(status_code=400, detail="Slot does not belong to the selected test")
    if slot.is_booked:
        raise HTTPException(status_code=400, detail="This slot is already booked")

    # Mark slot as booked
    slot.is_booked = True

    # Snapshot the price
    amount = test.price

    booking = Booking(
        user_id=user_id,
        test_id=test.id,
        centre_id=centre.id,
        slot_id=slot.id,
        appointment_datetime=slot.start_time,
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
    
    # Free up the slot if it's linked
    from app.models.centre import TestSlot
    if booking.slot_id:
        slot = db.query(TestSlot).filter(TestSlot.id == booking.slot_id).first()
        if slot:
            slot.is_booked = False

    db.commit()
    db.refresh(booking)
    return booking
