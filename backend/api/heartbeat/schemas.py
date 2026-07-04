"""
KOVIRX — Heartbeat Schemas.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class HeartbeatRequest(BaseModel):
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


class HeartbeatResponse(BaseModel):
    status: str = "ok"
    server_time: datetime
    next_heartbeat_seconds: int = 30
