"""
KOVIRX — Server-Side Risk Calculation Service.

Multi-source risk aggregation:
    ML Score (XGBoost + IF):     40% weight
    IOC Match Score:             25% weight
    Behavior Score:              25% weight
    Historical Device Score:     10% weight
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.risk_engine.schemas import (
    DailyRiskPoint,
    DeviceRiskHistoryResponse,
    RiskCalculateRequest,
    RiskCalculateResponse,
    RiskSourceBreakdown,
)
from database.models.ml import MLPrediction

logger = logging.getLogger("kovirx.risk_engine.service")


class RiskCalculationService:
    """
    Server-side multi-source risk score calculator.

    The agent computes ML + IOC + Behavior locally.
    The server adds Historical Score from device prediction history.
    """

    WEIGHT_ML = 0.40
    WEIGHT_IOC = 0.25
    WEIGHT_BEHAVIOR = 0.25
    WEIGHT_HISTORY = 0.10

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate(self, request: RiskCalculateRequest) -> RiskCalculateResponse:
        """Calculate multi-source risk score with server-side history."""
        # Compute history score from device's past predictions
        history_score = await self._compute_history_score(request.device_id)

        # ML score: combine XGBoost probability with anomaly flag
        anomaly_boost = 0.8 if request.is_anomaly else 0.0
        ml_combined = max(request.ml_score, anomaly_boost)

        # Weighted aggregation
        weighted = (
            (ml_combined * self.WEIGHT_ML)
            + (request.ioc_score * self.WEIGHT_IOC)
            + (request.behavior_score * self.WEIGHT_BEHAVIOR)
            + (history_score * self.WEIGHT_HISTORY)
        )

        risk_score = int(round(min(100, max(0, weighted * 100))))

        # Severity classification
        if risk_score >= 85:
            severity = "critical"
            recommendation = (
                "Quarantine endpoint immediately. Block outbound traffic. "
                "Initiate forensic investigation."
            )
        elif risk_score >= 60:
            severity = "high"
            recommendation = (
                "Trigger security investigation. Review processes and "
                "network connections on the endpoint."
            )
        elif risk_score >= 35:
            severity = "medium"
            recommendation = (
                "Enable enhanced monitoring. Review DNS queries and "
                "trace destination IPs."
            )
        else:
            severity = "low"
            recommendation = "No action required. Metrics within operational baseline."

        return RiskCalculateResponse(
            risk_score=risk_score,
            severity=severity,
            recommendation=recommendation,
            source_breakdown=RiskSourceBreakdown(
                ml_score=round(ml_combined, 4),
                ml_contribution=round(ml_combined * self.WEIGHT_ML * 100, 1),
                ioc_score=round(request.ioc_score, 4),
                ioc_contribution=round(request.ioc_score * self.WEIGHT_IOC * 100, 1),
                behavior_score=round(request.behavior_score, 4),
                behavior_contribution=round(request.behavior_score * self.WEIGHT_BEHAVIOR * 100, 1),
                history_score=round(history_score, 4),
                history_contribution=round(history_score * self.WEIGHT_HISTORY * 100, 1),
            ),
        )

    async def _compute_history_score(self, device_id: str) -> float:
        """
        Compute historical risk score for a device.

        Uses 7-day rolling average of past prediction confidence scores.
        Increasing frequency accelerates the score.
        """
        try:
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            result = await self.db.execute(
                select(
                    func.avg(MLPrediction.confidence_score),
                    func.count(MLPrediction.id),
                ).where(
                    MLPrediction.device_id == device_id,
                    MLPrediction.created_at >= week_ago,
                    MLPrediction.confidence_score >= 0.5,
                )
            )
            row = result.one()
            avg_score = float(row[0]) if row[0] else 0.0
            threat_count = int(row[1]) if row[1] else 0

            # Frequency acceleration: more threats = higher history score
            frequency_factor = min(1.0, threat_count / 20.0)

            return min(1.0, avg_score * (0.5 + 0.5 * frequency_factor))
        except Exception as e:
            logger.error("History score computation failed: %s", e)
            return 0.0

    async def get_device_history(
        self, device_id: UUID, days: int = 7
    ) -> DeviceRiskHistoryResponse:
        """Get daily average risk scores for the risk trend chart."""
        history: list[DailyRiskPoint] = []
        now = datetime.now(timezone.utc)

        for i in range(days):
            day_start = (now - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)

            try:
                result = await self.db.execute(
                    select(
                        func.avg(MLPrediction.confidence_score),
                        func.max(MLPrediction.confidence_score),
                        func.count(MLPrediction.id),
                    ).where(
                        MLPrediction.device_id == str(device_id),
                        MLPrediction.created_at >= day_start,
                        MLPrediction.created_at < day_end,
                    )
                )
                row = result.one()
                history.append(DailyRiskPoint(
                    date=day_start.strftime("%Y-%m-%d"),
                    avg_risk_score=round(float(row[0] or 0) * 100, 1),
                    max_risk_score=round(float(row[1] or 0) * 100, 1),
                    threat_count=int(row[2] or 0),
                ))
            except Exception:
                history.append(DailyRiskPoint(
                    date=day_start.strftime("%Y-%m-%d"),
                    avg_risk_score=0.0,
                    max_risk_score=0.0,
                    threat_count=0,
                ))

        history.reverse()

        return DeviceRiskHistoryResponse(
            device_id=str(device_id),
            days=days,
            history=history,
        )
