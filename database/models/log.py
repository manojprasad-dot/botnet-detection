"""
KOVIRX — Logging models.

SystemLog — application-level log entries (errors, warnings, info).
AuditLog  — security-critical action audit trail.
"""

import enum

from sqlalchemy import Enum, JSON, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin, UUIDMixin


class LogLevel(str, enum.Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class SystemLog(Base, UUIDMixin, TimestampMixin):
    """Application-level log entry."""

    __tablename__ = "system_logs"

    level: Mapped[LogLevel] = mapped_column(
        Enum(LogLevel, name="log_level"),
        nullable=False,
        index=True,
    )
    module: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """Security audit trail — tracks who did what and when."""

    __tablename__ = "audit_logs"

    user_id: Mapped[None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
