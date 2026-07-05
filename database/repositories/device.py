from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.device import Device, DeviceStatus
from database.repositories.base import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    async def get(self, db: AsyncSession, id: UUID) -> Device | None:
        result = await db.execute(select(Device).where(Device.id == id, Device.is_deleted == False))
        return result.scalar_one_or_none()

    async def get_by_hostname(self, db: AsyncSession, hostname: str) -> Device | None:
        result = await db.execute(select(Device).where(Device.hostname == hostname, Device.is_deleted == False))
        return result.scalar_one_or_none()

    async def list_devices(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
    ) -> tuple[int, list[Device]]:
        query = select(Device).where(Device.is_deleted == False)
        count_query = select(func.count(Device.id)).where(Device.is_deleted == False)

        if status:
            query = query.where(Device.status == status)
            count_query = count_query.where(Device.status == status)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        result = await db.execute(
            query.order_by(Device.created_at.desc()).offset(skip).limit(limit)
        )
        devices = list(result.scalars().all())
        return total, devices

    async def soft_delete(self, db: AsyncSession, device_id: UUID) -> bool:
        device = await db.get(Device, device_id)
        if device:
            device.is_deleted = True
            await db.flush()
            return True
        return False

    async def update_last_seen(self, db: AsyncSession, device_id: UUID) -> Device | None:
        device = await db.get(Device, device_id)
        if device:
            device.last_seen_at = datetime.now(timezone.utc)
            device.status = DeviceStatus.online
            await db.flush()
        return device

    async def update_risk_score(self, db: AsyncSession, device_id: UUID, risk_score: float) -> Device | None:
        device = await db.get(Device, device_id)
        if device:
            device.risk_score = min(100.0, max(0.0, risk_score))
            if risk_score >= 90:
                device.status = DeviceStatus.quarantined
            await db.flush()
        return device


device_repository = DeviceRepository(Device)
