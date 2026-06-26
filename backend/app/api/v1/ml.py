"""
KOVIRX — ML prediction routes: /api/v1/ml/*
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.ml import ModelStatusResponse, PredictRequest, PredictionListResponse, PredictionResponse
from app.services import ml_service

router = APIRouter(prefix="/ml", tags=["ML Detection"])


@router.post("/predict", response_model=list[PredictionResponse])
async def predict(
    data: PredictRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run ML prediction on given flow IDs."""
    return await ml_service.run_prediction(db, flow_ids=data.flow_ids)


@router.get("/predictions", response_model=PredictionListResponse)
async def list_predictions(
    device_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List past ML predictions with pagination."""
    return await ml_service.list_predictions(db, device_id=device_id, skip=skip, limit=limit)


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get prediction detail with SHAP explanation."""
    return await ml_service.get_prediction(db, prediction_id)


@router.get("/model-status", response_model=ModelStatusResponse)
async def model_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get model metadata and performance stats."""
    return await ml_service.get_model_status(db)
