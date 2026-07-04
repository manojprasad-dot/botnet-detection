"""
KOVIRX — Server-Side Behavior Analysis Routes.

Provides cross-network pattern detection by analyzing flow data
across all connected devices.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.api.behavior.schemas import (
    BehaviorAnalysisResponse,
    DeviceBehaviorResponse,
)
from backend.api.behavior.service import BehaviorAnalysisService
from database.session import get_db
from database.models.user import User

logger = logging.getLogger("kovirx.api.behavior")

router = APIRouter(prefix="/behavior", tags=["Behavior Analysis"])


@router.get("/overview", response_model=BehaviorAnalysisResponse)
async def get_behavior_overview(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get network-wide behavior analysis overview.

    Detects patterns across all devices: beaconing, scanning,
    lateral movement, DNS abuse, data exfiltration.
    """
    service = BehaviorAnalysisService(db)
    return await service.analyze_network(hours=hours)


@router.get("/device/{device_id}", response_model=DeviceBehaviorResponse)
async def get_device_behavior(
    device_id: UUID,
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get behavior analysis for a specific device.

    Returns detected behavioral patterns and confidence scores.
    """
    service = BehaviorAnalysisService(db)
    return await service.analyze_device(str(device_id), hours=hours)
