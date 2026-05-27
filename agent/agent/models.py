from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DeviceRegistration(BaseModel):
    device_fingerprint: str
    hostname: str
    ip_address: str | None = None
    operating_system: str
    os_version: str | None = None
    agent_version: str
    architecture: str | None = None
    tags: list[str] = Field(default_factory=list)


class TelemetryEvent(BaseModel):
    event_type: str
    source: str
    payload: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=utc_now)


class TelemetryBatch(BaseModel):
    device_id: str
    events: list[TelemetryEvent]
    generated_at: datetime = Field(default_factory=utc_now)
