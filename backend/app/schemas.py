from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OperatingSystem(str, Enum):
    windows = "windows"
    linux = "linux"
    macos = "macos"
    android = "android"
    iot = "iot"
    unknown = "unknown"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DeviceRegistration(BaseModel):
    device_fingerprint: str
    hostname: str
    ip_address: str | None = None
    operating_system: OperatingSystem = OperatingSystem.unknown
    os_version: str | None = None
    agent_version: str = "0.1.0"
    architecture: str | None = None
    tags: list[str] = Field(default_factory=list)


class RegisteredDevice(DeviceRegistration):
    device_id: str
    registered_at: datetime = Field(default_factory=utc_now)
    last_seen_at: datetime = Field(default_factory=utc_now)


class TelemetryEvent(BaseModel):
    event_type: str
    source: str
    payload: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=utc_now)


class TelemetryBatch(BaseModel):
    device_id: str
    events: list[TelemetryEvent]
    generated_at: datetime = Field(default_factory=utc_now)


class TelemetryRecord(TelemetryEvent):
    record_id: int
    device_id: str
    generated_at: datetime


class Alert(BaseModel):
    alert_id: str
    device_id: str
    severity: Severity
    title: str
    description: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=utc_now)
    evidence: dict[str, Any] = Field(default_factory=dict)


class TelemetryIngestResponse(BaseModel):
    ingested_events: int
    generated_alerts: list[Alert] = Field(default_factory=list)


class PlatformSummary(BaseModel):
    total_devices: int
    active_devices_24h: int
    total_events: int
    total_alerts: int
    alerts_by_severity: dict[str, int] = Field(default_factory=dict)
    events_by_type: dict[str, int] = Field(default_factory=dict)
    latest_alerts: list[Alert] = Field(default_factory=list)
