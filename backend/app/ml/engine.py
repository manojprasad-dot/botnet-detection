"""
KOVIRX — Detection Engine orchestrator.

Combines XGBoost and Isolation Forest predictions with SHAP explanations.
Initialised as a singleton on module import.
"""

import logging
from typing import Generator

from app.ml.explainer import explain_prediction
from app.ml.models.isolation_forest import IsolationForestDetector
from app.ml.models.xgboost_model import XGBoostDetector

logger = logging.getLogger("kovirx.ml.engine")


class DetectionEngine:
    """
    Unified detection engine that runs all loaded models.

    Usage:
        for model_name, result in detection_engine.predict(features):
            # process result
    """

    def __init__(self):
        self.xgboost = XGBoostDetector()
        self.iforest = IsolationForestDetector()
        logger.info(
            "DetectionEngine initialized — XGBoost: %s, IsolationForest: %s",
            "loaded" if self.xgboost.is_loaded else "heuristic",
            "loaded" if self.iforest.is_loaded else "heuristic",
        )

    def predict(self, features: list[float]) -> Generator[tuple[str, dict], None, None]:
        """
        Run all models and yield (model_name, result_dict) pairs.

        Each result dict contains:
            - confidence: float (0-1)
            - threat_type: str
            - explanation: dict | None (SHAP values)
        """
        # XGBoost prediction
        xgb_result = self.xgboost.predict(features)
        xgb_result["explanation"] = explain_prediction(
            self.xgboost.model, features
        )
        yield ("xgboost", xgb_result)

        # Isolation Forest prediction
        iforest_result = self.iforest.predict(features)
        iforest_result["explanation"] = None  # SHAP not applicable to IF
        yield ("isolation_forest", iforest_result)

    def get_model_info(self) -> list[dict]:
        """Return metadata about loaded models."""
        return [
            {
                "name": "xgboost",
                "type": "binary_classifier",
                "loaded": self.xgboost.is_loaded,
                "description": "XGBoost botnet vs benign classifier",
            },
            {
                "name": "isolation_forest",
                "type": "anomaly_detector",
                "loaded": self.iforest.is_loaded,
                "description": "Isolation Forest unsupervised anomaly detector",
            },
        ]


# Singleton instance — shared across the application
detection_engine = DetectionEngine()
