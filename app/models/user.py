"""
User model — mirrors Forehand's schema/user.ts (profileTable)
Stores authenticated user accounts with hashed passwords.
"""

import uuid
from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.common import created_at_col, updated_at_col


class User(Base):
    __tablename__ = "users"

    # Primary key — UUID generated at DB level (same as Forehand's uuid().primaryKey().defaultRandom())
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamps — from common.py (mirrors Forehand's createdAt/updatedAt)
    created_at: Mapped[object] = created_at_col()
    updated_at: Mapped[object] = updated_at_col()

    # Relations — one user can have many bookings
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="user", lazy="noload")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
