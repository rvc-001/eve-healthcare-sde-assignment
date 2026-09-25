"""
Payment Schemas
"""

from pydantic import BaseModel, Field
from app.models.enums import PaymentStatusEnum


class PaymentSimulateRequest(BaseModel):
    booking_id: str = Field(
        ...,
        description="The ID of the booking to process payment for.",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )


class PaymentWebhookRequest(BaseModel):
    booking_id: str = Field(
        ...,
        description="The booking ID this payment event relates to.",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    transaction_id: str = Field(
        ...,
        description="The provider-generated transaction reference.",
        examples=["txn_1f45a656d9cd45c8"]
    )
    status: PaymentStatusEnum = Field(
        ...,
        description="The outcome of the payment: SUCCESS or FAILED.",
        examples=["SUCCESS"]
    )
    idempotency_key: str = Field(
        ...,
        description=(
            "A unique key for this webhook event. The server uses this to safely "
            "deduplicate retried webhook deliveries without double-processing."
        ),
        examples=["idem_885904e2"]
    )
