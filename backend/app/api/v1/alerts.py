"""
KOVIRX — Alert routes: /api/v1/alerts/*
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.user import User
from app.schemas.alert import AlertAssignRequest, AlertListResponse, AlertResponse, AlertUpdateRequest
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    severity: str | None = None,
    status: str | None = None,
    device_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List alerts with pagination and filters."""
    return await alert_service.list_alerts(
        db, severity=severity, status=status, device_id=device_id,
        skip=skip, limit=limit,
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get alert detail."""
    return await alert_service.get_alert(db, alert_id)


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    data: AlertUpdateRequest,
    current_user: User = Depends(
        require_role("super_admin", "security_analyst", "soc_manager")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Update alert status (investigating, resolved, false_positive)."""
    return await alert_service.update_alert(db, alert_id, data)


@router.post("/{alert_id}/assign", response_model=AlertResponse)
async def assign_alert(
    alert_id: UUID,
    data: AlertAssignRequest,
    current_user: User = Depends(
        require_role("super_admin", "soc_manager")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Assign an alert to an analyst (manager + admin only)."""
    return await alert_service.assign_alert(db, alert_id, data.assigned_to)
