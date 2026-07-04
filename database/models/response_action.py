"""
KOVIRX — Response Action database model.

Audit trail for all automated and manual response actions.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from database.models.base import Base


class ResponseAction(Base):
    __tablename__ = "response_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String, nullable=False, index=True)
    action_type = Column(String, nullable=False)  # block_ip, quarantine, terminate, alert, notify
    target = Column(String, nullable=False)  # IP address, device UUID, threat type
    status = Column(String, default="pending")  # pending, executed, failed, reversed
    triggered_by = Column(String, default="auto")  # "auto" or user UUID
    risk_score = Column(Integer, default=0)
    alert_id = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
