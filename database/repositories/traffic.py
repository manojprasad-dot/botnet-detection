from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.traffic import NetworkFlow
from database.repositories.base import BaseRepository


class TrafficRepository(BaseRepository[NetworkFlow]):
    async def list_flows(
        self,
        db: AsyncSession,
        *,
        device_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[NetworkFlow]]:
        query = select(NetworkFlow)
        count_query = select(func.count(NetworkFlow.id))

        if device_id:
            query = query.where(NetworkFlow.device_id == device_id)
            count_query = count_query.where(NetworkFlow.device_id == device_id)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        result = await db.execute(
            query.order_by(NetworkFlow.created_at.desc()).offset(skip).limit(limit)
        )
        flows = list(result.scalars().all())
        return total, flows


traffic_repository = TrafficRepository(NetworkFlow)
