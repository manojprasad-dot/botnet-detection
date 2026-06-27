"""
KOVIRX — Device schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceCreateRequest(BaseModel):
    hostname: str = Field(max_length=255)
    operating_system: str = "unknown"
    mac_address: str | None = None
    ip_address: str | None = None
    agent_version: str = "0.1.0"
    os_version: str | None = None
    architecture: str | None = None
    tags: list[str] = Field(default_factory=list)


class DeviceUpdateRequest(BaseModel):
    hostname: str | None = None
    operating_system: str | None = None
    mac_address: str | None = None
    ip_address: str | None = None
    status: str | None = None
    agent_version: str | None = None
    os_version: str | None = None
    architecture: str | None = None
    tags: list[str] | None = None


class DeviceResponse(BaseModel):
    id: UUID
    hostname: str
    operating_system: str
    mac_address: str | None = None
    ip_address: str | None = None
    status: str
    risk_score: float
    agent_version: str
    os_version: str | None = None
    architecture: str | None = None
    tags: list | None = None
    last_seen_at: datetime | None = None
    registered_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceListResponse(BaseModel):
    total: int
    devices: list[DeviceResponse]
