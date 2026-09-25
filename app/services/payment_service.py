"""
Payment Service (Mock Gateway)
"""

import random
import uuid
from app.models.enums import PaymentStatusEnum


def simulate_payment() -> tuple[str, PaymentStatusEnum]:
    """
    Simulates a third-party payment gateway processing a payment.
    Randomly decides if the payment is SUCCESS (80% chance) or FAILED (20% chance).
    Returns a mock transaction ID and the status.
    """
    status = random.choices(
        [PaymentStatusEnum.SUCCESS, PaymentStatusEnum.FAILED],
        weights=[0.8, 0.2],
        k=1
    )[0]
    
    transaction_id = f"txn_{uuid.uuid4().hex[:16]}"
    return transaction_id, status


from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.payment import Payment
from app.models.booking import Booking
from app.models.enums import BookingStatusEnum
from app.schemas.payment import PaymentWebhookRequest


def process_webhook(db: Session, payload: PaymentWebhookRequest):
    """
    Process an incoming payment webhook idempotently.
    Returns early if the idempotency_key has already been processed.
    Updates the booking status based on the payment result.
    """
    # 1. Idempotency Check: Have we seen this key before?
    existing_payment = db.query(Payment).filter(Payment.idempotency_key == payload.idempotency_key).first()
    if existing_payment:
        return {"message": "Webhook already processed (idempotent success)."}

    # 2. Validate Booking exists
    booking = db.query(Booking).filter(Booking.id == payload.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found for this payment.")

    # 3. Create the payment record with the unique idempotency_key
    payment = Payment(
        booking_id=booking.id,
        status=payload.status,
        idempotency_key=payload.idempotency_key,
        provider_payment_id=payload.transaction_id,
    )
    db.add(payment)

    # 4. Update the Booking status
    if payload.status == PaymentStatusEnum.SUCCESS:
        booking.status = BookingStatusEnum.CONFIRMED
    else:
        booking.status = BookingStatusEnum.FAILED

    try:
        db.commit()
    except IntegrityError:
        # Race condition catch: if another request inserted this idempotency key at the exact same millisecond
        db.rollback()
        return {"message": "Webhook already processed (caught via DB unique constraint)."}

    return {"message": "Webhook processed successfully."}
