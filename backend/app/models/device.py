"""
KOVIRX — Device model.

Represents an endpoint agent registered with the platform.
"""

import enum

from sqlalchemy import Enum, Float, Integer, JSON, String, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class DeviceStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    quarantined = "quarantined"


class OperatingSystem(str, enum.Enum):
    windows = "windows"
    linux = "linux"
    macos = "macos"
    android = "android"
    iot = "iot"
    unknown = "unknown"


class Device(Base, UUIDMixin, TimestampMixin):
    """Registered endpoint device."""

    __tablename__ = "devices"

    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    operating_system: Mapped[str] = mapped_column(
        String(64),
        default="unknown",
        nullable=False,
    )
    mac_address: Mapped[str | None] = mapped_column(String(17), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus, name="device_status"),
        default=DeviceStatus.online,
        nullable=False,
    )
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    agent_version: Mapped[str] = mapped_column(String(20), default="0.1.0", nullable=False)
    os_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    architecture: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSON, default=list, nullable=True)
    last_seen_at: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Foreign key to the user who registered this device
    registered_by: Mapped[None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Device {self.hostname} status={self.status.value}>"
