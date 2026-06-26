"""
KOVIRX — Dashboard schemas.
"""

from pydantic import BaseModel


class TrafficStats(BaseModel):
    total_flows: int = 0
    suspicious_flows: int = 0
    blocked_flows: int = 0


class ThreatTypeStat(BaseModel):
    threat_type: str
    count: int


class DashboardSummaryResponse(BaseModel):
    protected_devices: int = 0
    active_threats: int = 0
    today_alerts: int = 0
    detection_accuracy: float = 0.0
    botnet_attempts_24h: int = 0
    traffic_stats: TrafficStats = TrafficStats()
    top_threat_types: list[ThreatTypeStat] = []
    severity_breakdown: dict[str, int] = {}
