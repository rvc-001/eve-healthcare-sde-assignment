"""
Diagnostic Centre & Test Schemas
"""

from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import datetime


class TestSlotResponse(BaseModel):
    id: str
    test_id: str
    start_time: datetime
    end_time: datetime
    is_booked: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DiagnosticTestResponse(BaseModel):
    id: str
    centre_id: str
    name: str
    description: str | None
    price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestWithSlotsResponse(DiagnosticTestResponse):
    available_slots: list[TestSlotResponse]


class DiagnosticCentreResponse(BaseModel):
    id: str
    name: str
    location: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CentreWithTestsResponse(DiagnosticCentreResponse):
    tests: list[DiagnosticTestResponse]
