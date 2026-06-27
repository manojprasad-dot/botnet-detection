"""
KOVIRX Platform — SQLAlchemy declarative base and common mixins.

Every model inherits from ``Base`` and gets UUID primary key,
``created_at``, and ``updated_at`` columns automatically.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, UUID, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base shared by all models."""
    pass


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` to any model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UUIDMixin:
    """Adds a UUID primary key column ``id``."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
