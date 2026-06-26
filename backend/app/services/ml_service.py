"""
KOVIRX — ML prediction service.

Orchestrates inference through XGBoost + Isolation Forest and stores results.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.ml.engine import detection_engine
from app.models.ml import MLPrediction, RiskLevel
from app.models.traffic import NetworkFlow
from app.schemas.ml import ModelStatusResponse, PredictionListResponse, PredictionResponse
from app.services.feature_service import compute_features_from_flows

logger = logging.getLogger("kovirx.ml")


def _confidence_to_risk_level(confidence: float) -> RiskLevel:
    """Map a confidence score to a risk level enum."""
    if confidence >= settings.ml_confidence_critical:
        return RiskLevel.critical
    elif confidence >= settings.ml_confidence_high:
        return RiskLevel.high
    elif confidence >= settings.ml_confidence_medium:
        return RiskLevel.medium
    elif confidence > 0.2:
        return RiskLevel.low
    return RiskLevel.safe


async def run_prediction(
    db: AsyncSession,
    flow_ids: list[UUID],
) -> list[PredictionResponse]:
    """
    Run ML prediction on a set of flows.

    Pipeline: flows → feature extraction → model inference → store predictions.
    """
    # Load flows
    result = await db.execute(
        select(NetworkFlow).where(NetworkFlow.id.in_(flow_ids))
    )
    flows = list(result.scalars().all())
    if not flows:
        raise NotFoundException("Flows")

    features = compute_features_from_flows(flows)
    feature_dict = features.model_dump()
    feature_array = list(feature_dict.values())

    # Get device_id from first flow
    device_id = flows[0].device_id

    predictions: list[PredictionResponse] = []

    # Run both models
    for model_name, result_data in detection_engine.predict(feature_array):
        confidence = result_data["confidence"]
        risk_level = _confidence_to_risk_level(confidence)
        explanation = result_data.get("explanation")

        pred = MLPrediction(
            device_id=device_id,
            flow_id=flows[0].id if flows else None,
            model_name=model_name,
            threat_type=result_data.get("threat_type", "botnet"),
            confidence_score=round(confidence, 4),
            risk_level=risk_level,
            explanation=explanation,
            features_used=feature_dict,
        )
        db.add(pred)
        await db.flush()
        await db.refresh(pred)
        predictions.append(PredictionResponse.model_validate(pred))

    logger.info(
        "ML predictions generated for device %s: %d results",
        device_id, len(predictions),
    )
    return predictions


async def list_predictions(
    db: AsyncSession,
    device_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> PredictionListResponse:
    """Return paginated prediction history."""
    query = select(MLPrediction)
    count_query = select(func.count(MLPrediction.id))

    if device_id:
        query = query.where(MLPrediction.device_id == device_id)
        count_query = count_query.where(MLPrediction.device_id == device_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(MLPrediction.created_at.desc()).offset(skip).limit(limit)
    )
    preds = [PredictionResponse.model_validate(p) for p in result.scalars().all()]
    return PredictionListResponse(total=total, predictions=preds)


async def get_prediction(db: AsyncSession, prediction_id: UUID) -> PredictionResponse:
    """Get a single prediction with SHAP explanation."""
    result = await db.execute(
        select(MLPrediction).where(MLPrediction.id == prediction_id)
    )
    pred = result.scalar_one_or_none()
    if not pred:
        raise NotFoundException("Prediction")
    return PredictionResponse.model_validate(pred)


async def get_model_status(db: AsyncSession) -> ModelStatusResponse:
    """Return model metadata and stats."""
    total_result = await db.execute(select(func.count(MLPrediction.id)))
    total = total_result.scalar() or 0

    models = detection_engine.get_model_info()

    return ModelStatusResponse(
        models=models,
        last_trained=None,  # Updated when retraining occurs
        total_predictions=total,
    )
