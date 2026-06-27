"""
KOVIRX — Dashboard routes: /api/v1/dashboard/*
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from database.session import get_db
from database.models.user import User
from backend.schemas.dashboard import DashboardSummaryResponse
from backend.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregated dashboard metrics."""
    return await dashboard_service.get_dashboard_summary(db)
