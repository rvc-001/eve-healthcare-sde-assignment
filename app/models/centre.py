"""
Diagnostic Centre and DiagnosticTest models.
Maps to the 'diagnostic_centres' and 'diagnostic_tests' tables.
"""

import uuid
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.common import created_at_col, updated_at_col


class DiagnosticCentre(Base):
    __tablename__ = "diagnostic_centres"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[object] = created_at_col()
    updated_at: Mapped[object] = updated_at_col()

    # Relations
    tests: Mapped[list["DiagnosticTest"]] = relationship(
        "DiagnosticTest", back_populates="centre", lazy="noload"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="centre", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<DiagnosticCentre id={self.id} name={self.name}>"


class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    centre_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("diagnostic_centres.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    created_at: Mapped[object] = created_at_col()
    updated_at: Mapped[object] = updated_at_col()

    # Relations
    centre: Mapped["DiagnosticCentre"] = relationship(
        "DiagnosticCentre", back_populates="tests", lazy="noload"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="test", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<DiagnosticTest id={self.id} name={self.name} price={self.price}>"
