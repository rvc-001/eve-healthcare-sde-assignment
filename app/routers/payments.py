"""
Payments Router (Mock Gateway)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.payment import PaymentSimulateRequest, PaymentWebhookRequest
from app.services import payment_service
from app.utils.response import send_response

router = APIRouter(prefix="/payments", tags=["Payments (Mock)"])


@router.post("/", summary="Simulate a Payment Gateway")
def simulate_payment_gateway(payload: PaymentSimulateRequest):
    """
    Simulates a 3rd party payment gateway (like Stripe or Razorpay).
    Takes a booking_id and randomly returns a SUCCESS (80%) or FAILED (20%) status
    along with a mock transaction ID.
    """
    transaction_id, status = payment_service.simulate_payment()

    return send_response(
        success=True,
        message="Payment processed by mock gateway.",
        data={
            "booking_id": payload.booking_id,
            "transaction_id": transaction_id,
            "status": status.value
        }
    )


@router.post("/webhook", summary="Payment Webhook Receiver")
def payment_webhook(
    payload: PaymentWebhookRequest,
    db: Session = Depends(get_db)
):
    """
    Receives async payment updates (SUCCESS/FAILED) from the payment gateway.
    Uses 'idempotency_key' to ensure the exact same webhook event is never
    processed twice — even under race conditions. Updates the booking to
    CONFIRMED or FAILED accordingly.
    """
    result = payment_service.process_webhook(db, payload)
    return send_response(
        success=True,
        message=result["message"]
    )
