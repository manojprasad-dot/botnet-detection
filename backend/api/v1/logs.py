"""
KOVIRX — Log routes: /api/v1/logs/*
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import require_role
from database.session import get_db
from database.models.user import User
from backend.schemas.log import AuditLogResponse, LogListResponse, SystemLogResponse
from backend.services import log_service

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/system")
async def get_system_logs(
    level: str | None = None,
    module: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Query system logs (admin only)."""
    total, logs = await log_service.query_system_logs(
        db, level=level, module=module, skip=skip, limit=limit,
    )
    return {
        "total": total,
        "logs": [SystemLogResponse.model_validate(l) for l in logs],
    }


@router.get("/audit")
async def get_audit_logs(
    user_id: UUID | None = None,
    action: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Query audit logs (admin only)."""
    total, logs = await log_service.query_audit_logs(
        db, user_id=user_id, action=action, skip=skip, limit=limit,
    )
    return {
        "total": total,
        "logs": [AuditLogResponse.model_validate(l) for l in logs],
    }


@router.get("/threats")
async def get_threat_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(
        require_role("super_admin", "security_analyst", "soc_manager")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Query threat detection logs."""
    total, logs = await log_service.query_system_logs(
        db, module="kovirx.ml", skip=skip, limit=limit,
    )
    return {
        "total": total,
        "logs": [SystemLogResponse.model_validate(l) for l in logs],
    }
