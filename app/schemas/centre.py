"""
Diagnostic Centre & Test Schemas
"""

from decimal import Decimal
from pydantic import BaseModel
from datetime import datetime


class DiagnosticTestResponse(BaseModel):
    id: str
    centre_id: str
    name: str
    description: str | None
    price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DiagnosticCentreResponse(BaseModel):
    id: str
    name: str
    location: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CentreWithTestsResponse(DiagnosticCentreResponse):
    tests: list[DiagnosticTestResponse]
