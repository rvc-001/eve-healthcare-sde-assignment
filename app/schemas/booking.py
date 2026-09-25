"""
Booking Schemas
"""

from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.enums import BookingStatusEnum
from app.schemas.centre import DiagnosticTestResponse, DiagnosticCentreResponse


class BookingCreateRequest(BaseModel):
    test_id: str = Field(..., description="The ID of the diagnostic test to book.", examples=["123e4567-e89b-12d3-a456-426614174000"])
    centre_id: str = Field(..., description="The ID of the diagnostic centre offering the test.", examples=["987e6543-e21b-34d5-c678-426614174999"])
    appointment_datetime: datetime = Field(..., description="The scheduled date and time for the test.", examples=["2026-10-10T10:00:00Z"])


class BookingResponse(BaseModel):
    id: str
    user_id: str
    test_id: str
    centre_id: str
    appointment_datetime: datetime
    amount: Decimal
    status: BookingStatusEnum
    created_at: datetime
    updated_at: datetime

    # Include nested relations for convenience
    test: DiagnosticTestResponse | None = None
    centre: DiagnosticCentreResponse | None = None

    model_config = {"from_attributes": True}
