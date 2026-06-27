"""
KOVIRX — Feature extraction routes: /api/v1/features/*
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from database.session import get_db
from database.models.user import User
from backend.schemas.feature import DeviceFeatureResponse, FeatureExtractRequest, FeatureVector
from backend.services import feature_service

router = APIRouter(prefix="/features", tags=["Feature Extraction"])


@router.post("/extract", response_model=FeatureVector)
async def extract_features(
    data: FeatureExtractRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Extract feature vector from given flow IDs."""
    return await feature_service.extract_features_for_flows(db, flow_ids=data.flow_ids)


@router.get("/device/{device_id}", response_model=DeviceFeatureResponse)
async def get_device_features(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest computed features for a device."""
    return await feature_service.get_device_features(db, device_id=device_id)
