"""
KOVIRX — Alert service.

Auto-generates alerts from ML predictions and manages alert lifecycle.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.exceptions import NotFoundException
from database.models.alert import AlertSeverity, AlertStatus
from database.repositories.alert import alert_repository
from backend.schemas.alert import AlertListResponse, AlertResponse, AlertUpdateRequest
from backend.schemas.ml import PredictionResponse

logger = logging.getLogger("kovirx.alerts")


def _confidence_to_severity(confidence: float) -> AlertSeverity:
    """Map ML confidence to alert severity."""
    if confidence >= settings.ml_confidence_critical:
        return AlertSeverity.critical
    elif confidence >= settings.ml_confidence_high:
        return AlertSeverity.high
    elif confidence >= settings.ml_confidence_medium:
        return AlertSeverity.medium
    return AlertSeverity.low


async def create_alert_from_prediction(
    db: AsyncSession,
    prediction: PredictionResponse,
) -> AlertResponse | None:
    """Auto-generate an alert if prediction confidence exceeds medium threshold."""
    if prediction.confidence_score < settings.ml_confidence_medium:
        return None  # Below threshold, no alert

    severity = _confidence_to_severity(prediction.confidence_score)

    alert_data = {
        "device_id": prediction.device_id,
        "prediction_id": prediction.id,
        "severity": severity,
        "title": f"{prediction.threat_type.upper()} detected by {prediction.model_name}",
        "description": (
            f"AI model '{prediction.model_name}' detected {prediction.threat_type} "
            f"activity with {prediction.confidence_score:.1%} confidence. "
            f"Risk level: {prediction.risk_level}."
        ),
        "evidence": {
            "model": prediction.model_name,
            "confidence": prediction.confidence_score,
            "risk_level": prediction.risk_level,
            "features": prediction.features_used,
            "explanation": prediction.explanation,
        },
    }
    alert = await alert_repository.create(db, obj_in=alert_data)
    await db.refresh(alert)
    logger.warning("ALERT generated: %s (severity=%s)", alert.title, severity.value)
    return AlertResponse.model_validate(alert)


async def list_alerts(
    db: AsyncSession,
    severity: str | None = None,
    status: str | None = None,
    device_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> AlertListResponse:
    """Return paginated alerts with optional filters."""
    total, alerts = await alert_repository.list_alerts(
        db, severity=severity, status=status, device_id=device_id, skip=skip, limit=limit
    )
    return AlertListResponse(total=total, alerts=[AlertResponse.model_validate(a) for a in alerts])


async def get_alert(db: AsyncSession, alert_id: UUID) -> AlertResponse:
    """Get a single alert."""
    alert = await alert_repository.get(db, alert_id)
    if not alert:
        raise NotFoundException("Alert")
    return AlertResponse.model_validate(alert)


async def update_alert(
    db: AsyncSession,
    alert_id: UUID,
    data: AlertUpdateRequest,
) -> AlertResponse:
    """Update alert status or details."""
    alert = await alert_repository.get(db, alert_id)
    if not alert:
        raise NotFoundException("Alert")

    update_data = data.model_dump(exclude_unset=True)
    await alert_repository.update(db, db_obj=alert, obj_in=update_data)
    await db.refresh(alert)
    logger.info("Alert %s updated: %s", alert_id, update_data)
    return AlertResponse.model_validate(alert)


async def assign_alert(
    db: AsyncSession,
    alert_id: UUID,
    assigned_to: UUID,
) -> AlertResponse:
    """Assign an alert to an analyst."""
    alert = await alert_repository.assign_alert(db, alert_id, assigned_to)
    if not alert:
        raise NotFoundException("Alert")
    await db.refresh(alert)
    logger.info("Alert %s assigned to %s", alert_id, assigned_to)
    return AlertResponse.model_validate(alert)
