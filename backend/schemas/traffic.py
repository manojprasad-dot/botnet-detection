"""
KOVIRX — Traffic schemas.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class FlowIngestRequest(BaseModel):
    """Single network flow submitted by an endpoint agent."""
    device_id: UUID
    source_ip: str
    source_port: int | None = None
    dest_ip: str
    dest_port: int | None = None
    protocol: str = "TCP"
    packet_count: int = 0
    byte_count: int = 0
    flow_duration: float = 0.0
    tcp_flags: str | None = None
    dns_query: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class FlowBatchIngestRequest(BaseModel):
    """Batch of flows from an agent."""
    device_id: UUID
    flows: list[FlowIngestRequest] = Field(default_factory=list)

    # Legacy telemetry compat — accepts old-style events too
    events: list[dict[str, Any]] = Field(default_factory=list)


class FlowResponse(BaseModel):
    id: UUID
    device_id: UUID
    source_ip: str
    source_port: int | None = None
    dest_ip: str
    dest_port: int | None = None
    protocol: str
    packet_count: int
    byte_count: int
    flow_duration: float
    tcp_flags: str | None = None
    dns_query: str | None = None
    dns_entropy: float | None = None
    beacon_interval: float | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FlowListResponse(BaseModel):
    total: int
    flows: list[FlowResponse]


class TrafficIngestResponse(BaseModel):
    ingested_flows: int
    generated_alerts: int
