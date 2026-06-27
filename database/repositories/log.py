from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.log import AuditLog, SystemLog, LogLevel
from database.repositories.base import BaseRepository


class SystemLogRepository(BaseRepository[SystemLog]):
    async def list_system_logs(
        self,
        db: AsyncSession,
        *,
        level: str | None = None,
        module: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[int, list[SystemLog]]:
        query = select(SystemLog)
        count_query = select(func.count(SystemLog.id))

        if level:
            query = query.where(SystemLog.level == level)
            count_query = count_query.where(SystemLog.level == level)
        if module:
            query = query.where(SystemLog.module == module)
            count_query = count_query.where(SystemLog.module == module)

        total = (await db.execute(count_query)).scalar() or 0
        result = await db.execute(
            query.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit)
        )
        return total, list(result.scalars().all())


class AuditLogRepository(BaseRepository[AuditLog]):
    async def list_audit_logs(
        self,
        db: AsyncSession,
        *,
        user_id: UUID | None = None,
        action: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[int, list[AuditLog]]:
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))

        if user_id:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)

        total = (await db.execute(count_query)).scalar() or 0
        result = await db.execute(
            query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        )
        return total, list(result.scalars().all())


system_log_repository = SystemLogRepository(SystemLog)
audit_log_repository = AuditLogRepository(AuditLog)
