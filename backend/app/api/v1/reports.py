"""
KOVIRX — Report routes: /api/v1/reports/*
"""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.exceptions import NotFoundException
from app.database.session import get_db
from app.models.user import User
from app.schemas.report import ReportGenerateRequest, ReportResponse
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportResponse, status_code=201)
async def generate_report(
    data: ReportGenerateRequest,
    current_user: User = Depends(
        require_role("super_admin", "soc_manager", "security_analyst")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Generate a daily/weekly/monthly report in PDF or CSV."""
    return await report_service.generate_report(db, report_type=data.report_type, fmt=data.format)


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
):
    """Download a generated report."""
    stored = report_service.get_report_content(report_id)
    if not stored:
        raise NotFoundException("Report")
    return Response(
        content=stored["content"],
        media_type=stored["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{stored["filename"]}"'},
    )


@router.get("")
async def list_reports(
    current_user: User = Depends(get_current_user),
):
    """List all generated reports."""
    return report_service.list_reports()
