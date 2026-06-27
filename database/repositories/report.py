from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.report import Report, ReportStatus
from database.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    async def get_by_id(self, db: AsyncSession, report_id: UUID) -> Report | None:
        return await db.get(self.model, report_id)

    async def list_reports(self, db: AsyncSession, *, skip: int = 0, limit: int = 50) -> list[Report]:
        query = select(Report).order_by(Report.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        db: AsyncSession,
        report_id: UUID,
        status: ReportStatus,
        content: bytes | None = None,
        error_message: str | None = None,
    ) -> Report | None:
        report = await db.get(Report, report_id)
        if report:
            report.status = status
            if content is not None:
                report.content = content
            if error_message is not None:
                report.error_message = error_message
            await db.flush()
        return report


report_repository = ReportRepository(Report)
