"""
KOVIRX — Device management service.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.device import Device
from app.schemas.device import DeviceCreateRequest, DeviceListResponse, DeviceResponse, DeviceUpdateRequest

logger = logging.getLogger("kovirx.devices")


async def create_device(
    db: AsyncSession,
    data: DeviceCreateRequest,
    registered_by: UUID | None = None,
) -> DeviceResponse:
    """Register a new device."""
    device = Device(
        hostname=data.hostname,
        operating_system=data.operating_system,
        mac_address=data.mac_address,
        ip_address=data.ip_address,
        agent_version=data.agent_version,
        os_version=data.os_version,
        architecture=data.architecture,
        tags=data.tags,
        last_seen_at=datetime.now(timezone.utc),
        registered_by=registered_by,
    )
    db.add(device)
    await db.flush()
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
    query = select(Device)
    count_query = select(func.count(Device.id))

    if status:
        query = query.where(Device.status == status)
        count_query = count_query.where(Device.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(Device.created_at.desc()).offset(skip).limit(limit)
    )
    devices = [DeviceResponse.model_validate(d) for d in result.scalars().all()]
    return DeviceListResponse(total=total, devices=devices)


async def get_device(db: AsyncSession, device_id: UUID) -> DeviceResponse:
    """Get a single device by ID."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise NotFoundException("Device")
    return DeviceResponse.model_validate(device)


async def update_device(
    db: AsyncSession,
    device_id: UUID,
    data: DeviceUpdateRequest,
) -> DeviceResponse:
    """Update device fields."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise NotFoundException("Device")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    await db.flush()
    await db.refresh(device)
    logger.info("Device updated: %s", device_id)
    return DeviceResponse.model_validate(device)


async def delete_device(db: AsyncSession, device_id: UUID) -> None:
    """Delete a device by ID."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise NotFoundException("Device")
    await db.delete(device)
    await db.flush()
    logger.info("Device deleted: %s", device_id)


async def update_device_last_seen(db: AsyncSession, device_id: UUID) -> None:
    """Update the last_seen_at timestamp for a device."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if device:
        device.last_seen_at = datetime.now(timezone.utc)
        device.status = "online"
        await db.flush()


async def update_device_risk_score(
    db: AsyncSession,
    device_id: UUID,
    risk_score: float,
) -> None:
    """Update the risk score based on latest ML prediction."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if device:
        device.risk_score = min(100.0, max(0.0, risk_score))
        if risk_score >= 90:
            device.status = "quarantined"
        await db.flush()
