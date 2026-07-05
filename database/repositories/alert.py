from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.alert import Alert, AlertStatus
from database.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    async def get(self, db: AsyncSession, id: UUID) -> Alert | None:
        result = await db.execute(select(Alert).where(Alert.id == id, Alert.is_deleted == False))
        return result.scalar_one_or_none()

    async def list_alerts(
        self,
        db: AsyncSession,
        *,
        severity: str | None = None,
        status: str | None = None,
        device_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[Alert]]:
        query = select(Alert).where(Alert.is_deleted == False)
        count_query = select(func.count(Alert.id)).where(Alert.is_deleted == False)

        if severity:
            query = query.where(Alert.severity == severity)
            count_query = count_query.where(Alert.severity == severity)
        if status:
            query = query.where(Alert.status == status)
            count_query = count_query.where(Alert.status == status)
        if device_id:
            query = query.where(Alert.device_id == device_id)
            count_query = count_query.where(Alert.device_id == device_id)

        total = (await db.execute(count_query)).scalar() or 0
        result = await db.execute(
            query.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
        )
        alerts = list(result.scalars().all())
        return total, alerts

    async def soft_delete(self, db: AsyncSession, alert_id: UUID) -> bool:
        alert = await db.get(Alert, alert_id)
        if alert:
            alert.is_deleted = True
            await db.flush()
            return True
        return False

    async def assign_alert(self, db: AsyncSession, alert_id: UUID, assigned_to: UUID) -> Alert | None:
        alert = await db.get(Alert, alert_id)
        if alert:
            alert.assigned_to = assigned_to
            alert.status = AlertStatus.investigating
            await db.flush()
        return alert


alert_repository = AlertRepository(Alert)
