"""
KOVIRX — Behavior Analysis Schemas.
"""

from pydantic import BaseModel, Field


class BehaviorPattern(BaseModel):
    pattern_type: str
    confidence: float
    description: str
    affected_devices: int = 0
    evidence: dict = Field(default_factory=dict)


class BehaviorAnalysisResponse(BaseModel):
    timeframe_hours: int
    total_patterns_detected: int
    patterns: list[BehaviorPattern]
    risk_summary: dict = Field(default_factory=dict)


class DeviceBehaviorPattern(BaseModel):
    pattern_type: str
    confidence: float
    description: str
    dest_ip: str | None = None
    first_seen: str | None = None
    last_seen: str | None = None


class DeviceBehaviorResponse(BaseModel):
    device_id: str
    timeframe_hours: int
    behavior_score: float
    patterns: list[DeviceBehaviorPattern]
