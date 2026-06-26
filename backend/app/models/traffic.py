"""
KOVIRX — Traffic and network-flow models.

TrafficLog  — raw telemetry ingestion record.
NetworkFlow — enriched per-flow record used for feature extraction.
"""

from sqlalchemy import DateTime, Float, Integer, String, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class TrafficLog(Base, UUIDMixin, TimestampMixin):
    """Raw traffic telemetry received from endpoint agents."""

    __tablename__ = "traffic_logs"

    device_id: Mapped[None] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    destination_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    protocol: Mapped[str] = mapped_column(String(10), nullable=False, default="TCP")
    packet_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    timestamp: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=False)
    flow_duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    connection_frequency: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class NetworkFlow(Base, UUIDMixin, TimestampMixin):
    """Enriched per-connection flow record for ML feature extraction."""

    __tablename__ = "network_flows"

    device_id: Mapped[None] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    source_port: Mapped[int] = mapped_column(Integer, nullable=True)
    dest_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    dest_port: Mapped[int] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str] = mapped_column(String(10), nullable=False, default="TCP")
    packet_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    byte_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flow_duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tcp_flags: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dns_query: Mapped[str | None] = mapped_column(String(512), nullable=True)
    dns_entropy: Mapped[float | None] = mapped_column(Float, nullable=True)
    beacon_interval: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_time: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)
