"""
Shared column definitions — mirrors Forehand's schema/common.ts
(createdAt / updatedAt columns reused across every table)
"""

import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import mapped_column, MappedColumn


def created_at_col() -> MappedColumn:
    return mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


def updated_at_col() -> MappedColumn:
    return mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
