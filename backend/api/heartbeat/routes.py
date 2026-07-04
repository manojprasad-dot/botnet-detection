"""
KOVIRX — Heartbeat API Routes.

Accepts periodic heartbeat payloads from endpoint agents containing
system metrics, agent status, and capture health indicators.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.api.heartbeat.schemas import HeartbeatRequest, HeartbeatResponse
from database.session import get_db
from database.models.user import User
from database.models.device import Device

logger = logging.getLogger("kovirx.api.heartbeat")

router = APIRouter(prefix="/devices", tags=["Heartbeat"])


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def receive_heartbeat(
    payload: HeartbeatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a heartbeat from an endpoint agent.

    Updates device last_seen_at and system metrics.
    Background task marks stale devices as offline.
    """
    # Update device last_seen_at and metrics
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Device).where(Device.id == UUID(payload.device_id))
    )
    device = result.scalar_one_or_none()

    if device:
        device.last_seen_at = now
        device.status = "online"
        await db.commit()
        logger.debug("Heartbeat from device %s. CPU=%.1f%% RAM=%.1f%%",
                      payload.device_id, payload.cpu_percent, payload.ram_percent)
    else:
        logger.warning("Heartbeat from unknown device: %s", payload.device_id)

    # Store heartbeat record
    from backend.api.heartbeat.service import store_heartbeat
    await store_heartbeat(db, payload)

    # Schedule stale device check
    background_tasks.add_task(mark_stale_devices_offline, db)

    return HeartbeatResponse(
        status="ok",
        server_time=now,
        next_heartbeat_seconds=30,
    )


async def mark_stale_devices_offline(db: AsyncSession) -> None:
    """Mark devices that haven't sent a heartbeat in >90 seconds as offline."""
    try:
        threshold = datetime.now(timezone.utc) - timedelta(seconds=90)
        await db.execute(
            update(Device)
            .where(Device.last_seen_at < threshold, Device.status == "online")
            .values(status="offline")
        )
        await db.commit()
    except Exception as e:
        logger.error("Failed to mark stale devices offline: %s", e)
