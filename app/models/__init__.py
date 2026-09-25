"""
Models package — mirrors Forehand's schema/index.ts (single barrel export).
Import all models here so Alembic and SQLAlchemy can discover them.
"""

from app.models.user import User
from app.models.centre import DiagnosticCentre, DiagnosticTest
from app.models.booking import Booking
from app.models.payment import Payment

__all__ = [
    "User",
    "DiagnosticCentre",
    "DiagnosticTest",
    "Booking",
    "Payment",
]
