"""
KOVIRX — Report routes: /api/v1/reports/*
"""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, require_role
from backend.core.exceptions import NotFoundException
from database.session import get_db
from database.models.user import User
from backend.schemas.report import ReportGenerateRequest, ReportResponse
from backend.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


from uuid import UUID

@router.post("/generate", response_model=ReportResponse, status_code=201)
async def generate_report(
    data: ReportGenerateRequest,
    current_user: User = Depends(
        require_role("super_admin", "soc_manager", "security_analyst")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Generate a daily/weekly/monthly report in PDF or CSV."""
    return await report_service.generate_report(db, report_type=data.report_type, fmt=data.format, generated_by=current_user.id)


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a generated report."""
    stored = await report_service.get_report_content(db, report_id)
    if not stored or not stored.content:
        raise NotFoundException("Report or report content not ready")
    return Response(
        content=stored.content,
        media_type="text/csv" if stored.format == "csv" else "application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{stored.filename}"'},
    )


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all generated reports."""
    return await report_service.list_reports(db)
