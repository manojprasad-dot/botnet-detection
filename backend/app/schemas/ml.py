"""
KOVIRX — ML prediction schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PredictRequest(BaseModel):
    flow_ids: list[UUID]


class PredictionResponse(BaseModel):
    id: UUID
    device_id: UUID
    flow_id: UUID | None = None
    model_name: str
    threat_type: str
    confidence_score: float
    risk_level: str
    explanation: dict | None = None
    features_used: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PredictionListResponse(BaseModel):
    total: int
    predictions: list[PredictionResponse]


class ModelStatusResponse(BaseModel):
    models: list[dict]
    last_trained: datetime | None = None
    total_predictions: int
