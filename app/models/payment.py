"""
Payment model — stores payment events linked to bookings.
The idempotency_key unique constraint is the core mechanism for
ensuring webhook events are processed exactly once.
"""

import uuid
from sqlalchemy import String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.common import created_at_col, updated_at_col
from app.models.enums import PaymentStatusEnum


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    booking_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[PaymentStatusEnum] = mapped_column(
        SAEnum(PaymentStatusEnum, name="payment_status_enum"),
        nullable=False,
    )

    # The idempotency_key guarantees that the same webhook event, delivered
    # multiple times, is safely deduplicated via a DB unique constraint.
    # On conflict → return early, skip processing. (Key design decision)
    idempotency_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )

    # Optional: provider-supplied payment reference (for real gateway integration later)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[object] = created_at_col()
    updated_at: Mapped[object] = updated_at_col()

    # Relations
    booking: Mapped["Booking"] = relationship("Booking", back_populates="payment", lazy="noload")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Payment id={self.id} status={self.status} idempotency_key={self.idempotency_key}>"
