"""
KOVIRX — Alert schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AlertUpdateRequest(BaseModel):
    status: str | None = None  # investigating, resolved, false_positive
    title: str | None = None
    description: str | None = None


class AlertAssignRequest(BaseModel):
    assigned_to: UUID


class AlertResponse(BaseModel):
    id: UUID
    device_id: UUID
    prediction_id: UUID | None = None
    severity: str
    title: str
    description: str | None = None
    status: str
    assigned_to: UUID | None = None
    evidence: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    total: int
    alerts: list[AlertResponse]
