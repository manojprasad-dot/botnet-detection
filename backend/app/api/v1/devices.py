"""
KOVIRX — Device routes: /api/v1/devices/*
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.user import User
from app.schemas.device import DeviceCreateRequest, DeviceListResponse, DeviceResponse, DeviceUpdateRequest
from app.services import device_service

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("/register", response_model=DeviceResponse, status_code=201)
async def register_device(
    data: DeviceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new endpoint device."""
    return await device_service.create_device(db, data, registered_by=current_user.id)


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all registered devices with pagination."""
    return await device_service.list_devices(db, skip=skip, limit=limit, status=status)


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get device details by ID."""
    return await device_service.get_device(db, device_id)


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    data: DeviceUpdateRequest,
    current_user: User = Depends(
        require_role("super_admin", "security_analyst")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Update device fields (analyst + admin only)."""
    return await device_service.update_device(db, device_id, data)


@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: UUID,
    current_user: User = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a device (admin only)."""
    await device_service.delete_device(db, device_id)
