"""
KOVIRX — Heartbeat Service.

Stores heartbeat records and provides device health analysis.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.heartbeat.schemas import HeartbeatRequest

logger = logging.getLogger("kovirx.heartbeat.service")


async def store_heartbeat(db: AsyncSession, payload: HeartbeatRequest) -> None:
    """
    Store a heartbeat record in the database.

    Uses the Heartbeat model if available, otherwise logs metrics.
    """
    try:
        from database.models.heartbeat import Heartbeat

        heartbeat = Heartbeat(
            device_id=payload.device_id,
            cpu_percent=payload.cpu_percent,
            ram_percent=payload.ram_percent,
            disk_percent=payload.disk_percent,
            uptime_seconds=payload.uptime_seconds,
            agent_version=payload.agent_version,
            capture_status=payload.capture_status,
            flows_processed=payload.flows_processed,
            packets_captured=payload.packets_captured,
            threats_detected=payload.threats_detected,
            queue_depth=payload.queue_depth,
        )
        db.add(heartbeat)
        await db.flush()
    except ImportError:
        logger.debug(
            "Heartbeat model not available yet. Metrics: CPU=%.1f%%, RAM=%.1f%%",
            payload.cpu_percent, payload.ram_percent,
        )
    except Exception as e:
        logger.error("Failed to store heartbeat: %s", e)
