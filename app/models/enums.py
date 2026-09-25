"""
Enum definitions — mirrors Forehand's schema/enums.ts
All pg enums are declared here and imported by table files.
"""

import enum


class BookingStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PaymentStatusEnum(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
