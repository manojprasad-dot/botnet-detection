from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from uuid import UUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TelemetryEvent(BaseModel):
    event_type: str
    source: str
    payload: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=utc_now)


class TelemetryBatch(BaseModel):
    device_id: str
    events: list[TelemetryEvent]
    generated_at: datetime = Field(default_factory=utc_now)


# ── New Telemetry Ingestion Schemas ────────────────────────────────
class FlowTelemetryData(BaseModel):
    source_ip: str
    source_port: int | None = None
    dest_ip: str
    dest_port: int | None = None
    protocol: str = "TCP"
    packet_count: int = 0
    byte_count: int = 0
    packets_sent: int = 0
    packets_recv: int = 0
    bytes_sent: int = 0
    bytes_recv: int = 0
    flow_duration: float = 0.0
    tcp_flags: str | None = None
    dns_query: str | None = None
    dns_entropy: float | None = None
    beacon_interval: float | None = None
    failed_connections: int = 0
    start_time: datetime
    end_time: datetime


class PredictionTelemetryData(BaseModel):
    xgb_score: float
    is_anomaly: bool
    threat_type: str
    features_used: dict[str, float]


class RiskTelemetryData(BaseModel):
    risk_score: int
    severity: Severity
    recommendation: str


class TelemetryEventItem(BaseModel):
    flow: FlowTelemetryData
    prediction: PredictionTelemetryData
    risk: RiskTelemetryData
    collected_at: datetime


class TelemetryIngestPayload(BaseModel):
    device_id: UUID
    events: list[TelemetryEventItem]
    generated_at: datetime


class TelemetryIngestResponse(BaseModel):
    ingested_flows: int
    generated_alerts: int
