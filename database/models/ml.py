"""
KOVIRX — ML prediction model.

Stores every inference result with its confidence score,
risk level, SHAP explanation, and feature snapshot.
"""

import enum

from sqlalchemy import Enum, Float, JSON, String, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin, UUIDMixin


class RiskLevel(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    safe = "safe"


class MLPrediction(Base, UUIDMixin, TimestampMixin):
    """Single ML inference result against a device or flow."""

    __tablename__ = "ml_predictions"

    device_id: Mapped[None] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    flow_id: Mapped[None] = mapped_column(UUID(as_uuid=True), nullable=True)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    threat_type: Mapped[str] = mapped_column(String(128), nullable=False, default="botnet")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level"),
        nullable=False,
    )
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # SHAP values
    features_used: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # feature snapshot

    def __repr__(self) -> str:
        return f"<MLPrediction model={self.model_name} risk={self.risk_level.value} conf={self.confidence_score:.2f}>"
