"""
KOVIRX — Risk Engine Schemas.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class RiskCalculateRequest(BaseModel):
    device_id: str
    ml_score: float = Field(ge=0.0, le=1.0)
    ioc_score: float = Field(ge=0.0, le=1.0, default=0.0)
    behavior_score: float = Field(ge=0.0, le=1.0, default=0.0)
    threat_type: str = "Unknown"
    is_anomaly: bool = False


class RiskSourceBreakdown(BaseModel):
    ml_score: float
    ml_contribution: float
    ioc_score: float
    ioc_contribution: float
    behavior_score: float
    behavior_contribution: float
    history_score: float
    history_contribution: float


class RiskCalculateResponse(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    severity: str
    recommendation: str
    source_breakdown: RiskSourceBreakdown


class DailyRiskPoint(BaseModel):
    date: str
    avg_risk_score: float
    max_risk_score: float
    threat_count: int


class DeviceRiskHistoryResponse(BaseModel):
    device_id: str
    days: int
    history: list[DailyRiskPoint]
