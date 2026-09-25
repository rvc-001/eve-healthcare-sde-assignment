"""
Booking model — joins user, diagnostic test, and centre.
Tracks appointment datetime, snapshotted price, and booking status.
"""

import uuid
from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.common import created_at_col, updated_at_col
from app.models.enums import BookingStatusEnum


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Foreign keys — mirrors Forehand's .references(() => profileTable.id) pattern
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("diagnostic_tests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    centre_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("diagnostic_centres.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    appointment_datetime: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Price snapshot: stores test price AT TIME OF BOOKING, not a live FK reference.
    # This ensures historical accuracy even if the test price changes later.
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    status: Mapped[BookingStatusEnum] = mapped_column(
        SAEnum(BookingStatusEnum, name="booking_status_enum"),
        nullable=False,
        default=BookingStatusEnum.PENDING,
        server_default=BookingStatusEnum.PENDING.value,
    )

    created_at: Mapped[object] = created_at_col()
    updated_at: Mapped[object] = updated_at_col()

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="bookings", lazy="noload")  # type: ignore[name-defined]
    test: Mapped["DiagnosticTest"] = relationship("DiagnosticTest", back_populates="bookings", lazy="noload")  # type: ignore[name-defined]
    centre: Mapped["DiagnosticCentre"] = relationship("DiagnosticCentre", back_populates="bookings", lazy="noload")  # type: ignore[name-defined]
    payment: Mapped["Payment"] = relationship("Payment", back_populates="booking", uselist=False, lazy="noload")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Booking id={self.id} status={self.status}>"
