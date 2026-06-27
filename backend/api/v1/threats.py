"""
KOVIRX — Threat intelligence routes: /api/v1/threats/*
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, require_role
from database.session import get_db
from database.models.user import User
from backend.schemas.threat import (
    BotnetFamilyCreateRequest, BotnetFamilyListResponse, BotnetFamilyResponse,
    IOCCheckRequest, IOCCheckResult, IOCCreateRequest, IOCListResponse, IOCResponse,
)
from backend.services import threat_service

router = APIRouter(prefix="/threats", tags=["Threat Intelligence"])


# ── IOCs ───────────────────────────────────────────────────────────
@router.get("/iocs", response_model=IOCListResponse)
async def list_iocs(
    ioc_type: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List IOCs with optional type filter."""
    return await threat_service.list_iocs(db, ioc_type=ioc_type, skip=skip, limit=limit)


@router.post("/iocs", response_model=IOCResponse, status_code=201)
async def create_ioc(
    data: IOCCreateRequest,
    current_user: User = Depends(
        require_role("super_admin", "security_analyst")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Add a new Indicator of Compromise."""
    return await threat_service.create_ioc(db, data)


@router.delete("/iocs/{ioc_id}", status_code=204)
async def delete_ioc(
    ioc_id: UUID,
    current_user: User = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Remove an IOC (admin only)."""
    await threat_service.delete_ioc(db, ioc_id)


@router.post("/iocs/check", response_model=list[IOCCheckResult])
async def check_iocs(
    data: IOCCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check a list of IPs/domains against threat intel."""
    return await threat_service.check_iocs(db, data)


# ── Botnet Families ────────────────────────────────────────────────
@router.get("/families", response_model=BotnetFamilyListResponse)
async def list_families(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List botnet families."""
    return await threat_service.list_botnet_families(db, skip=skip, limit=limit)


@router.post("/families", response_model=BotnetFamilyResponse, status_code=201)
async def create_family(
    data: BotnetFamilyCreateRequest,
    current_user: User = Depends(
        require_role("super_admin", "security_analyst")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Add a botnet family record."""
    return await threat_service.create_botnet_family(db, data)


@router.get("/families/{family_id}", response_model=BotnetFamilyResponse)
async def get_family(
    family_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get botnet family details."""
    return await threat_service.get_botnet_family(db, family_id)
