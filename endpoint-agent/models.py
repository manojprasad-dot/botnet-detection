"""
KOVIRX Endpoint Agent — Data Models.

Pydantic models for device registration, telemetry events, heartbeat payloads,
and internal agent state representation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ── Enums ─────────────────────────────────────────────────────────


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class CaptureStatus(str, Enum):
    active = "active"
    stopped = "stopped"
    error = "error"


# ── Device Registration ──────────────────────────────────────────


class DeviceRegistration(BaseModel):
    hostname: str
    ip_address: str | None = None
    mac_address: str | None = None
    operating_system: str
    os_version: str | None = None
    agent_version: str
    architecture: str | None = None
    cpu_model: str | None = None
    ram_total_gb: float | None = None
    tags: list[str] = Field(default_factory=list)


# ── Heartbeat ────────────────────────────────────────────────────


class HeartbeatPayload(BaseModel):
    device_id: str
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    disk_percent: float = 0.0
    uptime_seconds: int = 0
    agent_version: str = "1.0.0"
    capture_status: str = "active"
    flows_processed: int = 0
    packets_captured: int = 0
    threats_detected: int = 0
    queue_depth: int = 0


# ── Flow Telemetry ───────────────────────────────────────────────


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


class PredictionResult(BaseModel):
    xgb_score: float = 0.0
    is_anomaly: bool = False
    threat_type: str = "Normal"
    features_used: dict[str, float] = Field(default_factory=dict)


class RiskResult(BaseModel):
    risk_score: int = 0
    severity: Severity = Severity.low
    recommendation: str = ""
    behavior_score: float = 0.0
    intel_score: float = 0.0


class BehaviorResult(BaseModel):
    behavior_score: float = 0.0
    behavior_type: str = "normal"
    patterns_detected: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class TelemetryEventItem(BaseModel):
    flow: FlowTelemetryData
    prediction: PredictionResult
    risk: RiskResult
    behavior: BehaviorResult = Field(default_factory=BehaviorResult)
    collected_at: datetime = Field(default_factory=utc_now)


class TelemetryIngestPayload(BaseModel):
    device_id: str
    events: list[TelemetryEventItem]
    generated_at: datetime = Field(default_factory=utc_now)


# ── WebSocket Commands ───────────────────────────────────────────


class AgentCommand(BaseModel):
    """Command received from backend via WebSocket."""
    command: str  # block_ip, update_config, sync_ioc, restart_capture
    target: str | None = None  # IP address, config key, etc.
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


# ── Agent Metrics ────────────────────────────────────────────────


class AgentMetrics(BaseModel):
    """Internal agent state snapshot for health monitoring."""
    uptime_seconds: int = 0
    packets_captured: int = 0
    flows_processed: int = 0
    flows_uploaded: int = 0
    threats_detected: int = 0
    queue_depth: int = 0
    capture_status: CaptureStatus = CaptureStatus.active
    last_upload: datetime | None = None
    last_heartbeat: datetime | None = None
    blocked_ips: list[str] = Field(default_factory=list)
