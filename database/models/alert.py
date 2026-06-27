"""
KOVIRX — Alert model.

Security alerts generated from ML predictions or heuristic rules.
"""

import enum

from sqlalchemy import Enum, JSON, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin, UUIDMixin


class AlertSeverity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class AlertStatus(str, enum.Enum):
    new = "new"
    investigating = "investigating"
    resolved = "resolved"
    false_positive = "false_positive"


class Alert(Base, UUIDMixin, TimestampMixin):
    """Security alert tied to a device and optionally an ML prediction."""

    __tablename__ = "alerts"

    device_id: Mapped[None] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    prediction_id: Mapped[None] = mapped_column(UUID(as_uuid=True), nullable=True)
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alert_status"),
        default=AlertStatus.new,
        nullable=False,
        index=True,
    )
    assigned_to: Mapped[None] = mapped_column(UUID(as_uuid=True), nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Alert {self.title} severity={self.severity.value} status={self.status.value}>"
