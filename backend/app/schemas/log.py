"""
KOVIRX — Log schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SystemLogResponse(BaseModel):
    id: UUID
    level: str
    module: str
    message: str
    details: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None = None
    action: str
    resource: str
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    details: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LogListResponse(BaseModel):
    total: int
    logs: list[SystemLogResponse | AuditLogResponse]
