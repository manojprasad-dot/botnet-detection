"""
KOVIRX — Server-Side Risk Engine Routes.

Provides API endpoints for risk score queries, risk history,
and multi-source risk calculation on demand.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.api.risk_engine.schemas import (
    RiskCalculateRequest,
    RiskCalculateResponse,
    DeviceRiskHistoryResponse,
)
from backend.api.risk_engine.service import RiskCalculationService
from database.session import get_db
from database.models.user import User

logger = logging.getLogger("kovirx.api.risk_engine")

router = APIRouter(prefix="/risk", tags=["Risk Engine"])


@router.post("/calculate", response_model=RiskCalculateResponse)
async def calculate_risk(
    payload: RiskCalculateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate multi-source risk score for a telemetry event.

    Combines: ML Score (40%) + IOC Match (25%) + Behavior (25%) + History (10%)
    """
    service = RiskCalculationService(db)
    return await service.calculate(payload)


@router.get("/device/{device_id}/history", response_model=DeviceRiskHistoryResponse)
async def get_device_risk_history(
    device_id: UUID,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get historical risk scores for a device over a time period.

    Returns daily average risk scores for the risk trend chart.
    """
    service = RiskCalculationService(db)
    return await service.get_device_history(device_id, days=days)
