from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.ml import MLPrediction
from database.repositories.base import BaseRepository


class MLPredictionRepository(BaseRepository[MLPrediction]):
    async def list_predictions(
        self,
        db: AsyncSession,
        *,
        device_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[MLPrediction]]:
        query = select(MLPrediction)
        count_query = select(func.count(MLPrediction.id))

        if device_id:
            query = query.where(MLPrediction.device_id == device_id)
            count_query = count_query.where(MLPrediction.device_id == device_id)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        result = await db.execute(
            query.order_by(MLPrediction.created_at.desc()).offset(skip).limit(limit)
        )
        predictions = list(result.scalars().all())
        return total, predictions

    async def get_total_count(self, db: AsyncSession) -> int:
        result = await db.execute(select(func.count(MLPrediction.id)))
        return result.scalar() or 0


ml_prediction_repository = MLPredictionRepository(MLPrediction)
