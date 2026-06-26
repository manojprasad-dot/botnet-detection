"""
KOVIRX — Dashboard aggregation service.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertSeverity
from app.models.device import Device
from app.models.ml import MLPrediction
from app.models.traffic import NetworkFlow
from app.schemas.dashboard import DashboardSummaryResponse, ThreatTypeStat, TrafficStats

logger = logging.getLogger("kovirx.dashboard")


async def get_dashboard_summary(db: AsyncSession) -> DashboardSummaryResponse:
    """Aggregate key metrics for the dashboard overview."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_24h = now - timedelta(hours=24)

    # Protected devices (total registered)
    devices_total = (await db.execute(select(func.count(Device.id)))).scalar() or 0

    # Active threats (predictions with risk >= high in last 24h)
    active_threats = (await db.execute(
        select(func.count(MLPrediction.id)).where(
            MLPrediction.created_at >= last_24h,
            MLPrediction.risk_level.in_(["critical", "high"]),
        )
    )).scalar() or 0

    # Today's alerts
    today_alerts = (await db.execute(
        select(func.count(Alert.id)).where(Alert.created_at >= today_start)
    )).scalar() or 0

    # Detection accuracy (ratio of non-false-positive resolved alerts)
    total_resolved = (await db.execute(
        select(func.count(Alert.id)).where(Alert.status.in_(["resolved", "false_positive"]))
    )).scalar() or 0
    true_positives = (await db.execute(
        select(func.count(Alert.id)).where(Alert.status == "resolved")
    )).scalar() or 0
    accuracy = (true_positives / total_resolved * 100) if total_resolved > 0 else 98.0

    # Botnet attempts 24h
    botnet_24h = (await db.execute(
        select(func.count(MLPrediction.id)).where(
            MLPrediction.created_at >= last_24h,
            MLPrediction.confidence_score >= 0.5,
        )
    )).scalar() or 0

    # Traffic stats
    total_flows = (await db.execute(select(func.count(NetworkFlow.id)))).scalar() or 0
    suspicious_flows = (await db.execute(
        select(func.count(NetworkFlow.id)).where(NetworkFlow.dns_entropy > 4.0)
    )).scalar() or 0

    # Severity breakdown
    severity_breakdown: dict[str, int] = {}
    for sev in AlertSeverity:
        count = (await db.execute(
            select(func.count(Alert.id)).where(Alert.severity == sev)
        )).scalar() or 0
        severity_breakdown[sev.value] = count

    # Top threat types
    threat_type_query = await db.execute(
        select(MLPrediction.threat_type, func.count(MLPrediction.id).label("cnt"))
        .group_by(MLPrediction.threat_type)
        .order_by(func.count(MLPrediction.id).desc())
        .limit(5)
    )
    top_threats = [
        ThreatTypeStat(threat_type=row[0], count=row[1])
        for row in threat_type_query.all()
    ]

    return DashboardSummaryResponse(
        protected_devices=devices_total,
        active_threats=active_threats,
        today_alerts=today_alerts,
        detection_accuracy=round(accuracy, 1),
        botnet_attempts_24h=botnet_24h,
        traffic_stats=TrafficStats(
            total_flows=total_flows,
            suspicious_flows=suspicious_flows,
            blocked_flows=0,
        ),
        top_threat_types=top_threats,
        severity_breakdown=severity_breakdown,
    )
