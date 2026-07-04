"""
KOVIRX — Heartbeat database model.

Stores periodic heartbeat records from endpoint agents.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from database.models.base import Base


class Heartbeat(Base):
    __tablename__ = "heartbeats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String, nullable=False, index=True)
    cpu_percent = Column(Float, default=0.0)
    ram_percent = Column(Float, default=0.0)
    disk_percent = Column(Float, default=0.0)
    uptime_seconds = Column(Integer, default=0)
    agent_version = Column(String, default="1.0.0")
    capture_status = Column(String, default="active")
    flows_processed = Column(Integer, default=0)
    packets_captured = Column(Integer, default=0)
    threats_detected = Column(Integer, default=0)
    queue_depth = Column(Integer, default=0)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
