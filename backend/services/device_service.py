"""
KOVIRX — Device management service.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundException
from database.models.device import Device
from database.repositories.device import device_repository
from backend.schemas.device import DeviceCreateRequest, DeviceListResponse, DeviceResponse, DeviceUpdateRequest

logger = logging.getLogger("kovirx.devices")


async def create_device(
    db: AsyncSession,
    data: DeviceCreateRequest,
    registered_by: UUID | None = None,
) -> DeviceResponse:
    """Register a new device."""
    device_in = {
        "hostname": data.hostname,
        "operating_system": data.operating_system,
        "mac_address": data.mac_address,
        "ip_address": data.ip_address,
        "agent_version": data.agent_version,
        "os_version": data.os_version,
        "architecture": data.architecture,
        "tags": data.tags,
        "last_seen_at": datetime.now(timezone.utc),
        "registered_by": registered_by,
    }
    device = await device_repository.create(db, obj_in=device_in)
    await db.refresh(device)
    logger.info("Device registered: %s (%s)", device.hostname, device.id)
    return DeviceResponse.model_validate(device)


async def list_devices(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
) -> DeviceListResponse:
    """Return paginated device list with optional status filter."""
    total, devices = await device_repository.list_devices(db, skip=skip, limit=limit, status=status)
    return DeviceListResponse(
        total=total,
        devices=[DeviceResponse.model_validate(d) for d in devices]
    )


async def get_device(db: AsyncSession, device_id: UUID) -> DeviceResponse:
    """Get a single device by ID."""
    device = await device_repository.get(db, device_id)
    if not device:
        raise NotFoundException("Device")
    return DeviceResponse.model_validate(device)


async def update_device(
    db: AsyncSession,
    device_id: UUID,
    data: DeviceUpdateRequest,
) -> DeviceResponse:
    """Update device fields."""
    device = await device_repository.get(db, device_id)
    if not device:
        raise NotFoundException("Device")

    update_data = data.model_dump(exclude_unset=True)
    await device_repository.update(db, db_obj=device, obj_in=update_data)
    await db.refresh(device)
    logger.info("Device updated: %s", device_id)
    return DeviceResponse.model_validate(device)


async def delete_device(db: AsyncSession, device_id: UUID) -> None:
    """Delete a device by ID (soft delete)."""
    success = await device_repository.soft_delete(db, device_id)
    if not success:
        raise NotFoundException("Device")
    logger.info("Device soft-deleted: %s", device_id)


async def update_device_last_seen(db: AsyncSession, device_id: UUID) -> None:
    """Update the last_seen_at timestamp for a device."""
    await device_repository.update_last_seen(db, device_id)


async def update_device_risk_score(
    db: AsyncSession,
    device_id: UUID,
    risk_score: float,
) -> None:
    """Update the risk score based on latest ML prediction."""
    await device_repository.update_risk_score(db, device_id, risk_score)
