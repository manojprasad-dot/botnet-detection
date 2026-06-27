"""
KOVIRX — Dashboard aggregation service.
"""

import logging
from datetime import datetime, timedelta, timezone

import redis.asyncio as redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from database.models.alert import Alert, AlertSeverity
from database.models.device import Device
from database.models.ml import MLPrediction
from database.models.traffic import NetworkFlow
from backend.schemas.dashboard import DashboardSummaryResponse, ThreatTypeStat, TrafficStats

logger = logging.getLogger("kovirx.dashboard")

redis_client = None


def get_redis_client():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return redis_client


async def get_dashboard_summary(db: AsyncSession) -> DashboardSummaryResponse:
    """Aggregate key metrics for the dashboard overview, caching in Redis."""
    r = get_redis_client()
    try:
        cached = await r.get("kovirx:dashboard_summary")
        if cached:
            logger.info("Dashboard summary cache hit")
            return DashboardSummaryResponse.model_validate_json(cached)
    except Exception as e:
        logger.warning("Redis cache error (falling back to database): %s", e)

    logger.info("Dashboard summary cache miss — querying database")
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

    summary = DashboardSummaryResponse(
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

    try:
        await r.set("kovirx:dashboard_summary", summary.model_dump_json(), ex=10)
    except Exception as e:
        logger.warning("Failed to write to Redis cache: %s", e)

    return summary
