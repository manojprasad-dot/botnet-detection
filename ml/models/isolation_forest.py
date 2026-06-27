"""
KOVIRX — Isolation Forest anomaly detector wrapper.

Detects anomalous network flow patterns using unsupervised learning.
"""

import logging
import os

import joblib
import numpy as np

logger = logging.getLogger("kovirx.ml.iforest")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "saved_models", "isolation_forest.pkl")


class IsolationForestDetector:
    """Wrapper around scikit-learn IsolationForest for anomaly detection."""

    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load a pre-trained model from disk."""
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                logger.info("IsolationForest model loaded from %s", MODEL_PATH)
            except Exception as e:
                logger.warning("Failed to load IsolationForest model: %s", e)
                self.model = None
        else:
            logger.info("No pre-trained IsolationForest model found, using fallback")

    def predict(self, features: list[float]) -> dict:
        """
        Run anomaly detection on a feature vector.

        Returns:
            dict with 'confidence', 'threat_type', 'is_anomaly', 'anomaly_score'
        """
        feature_array = np.array(features).reshape(1, -1)

        if self.model is not None:
            try:
                # IsolationForest: -1 = anomaly, 1 = normal
                prediction = int(self.model.predict(feature_array)[0])
                # score_samples returns negative log-likelihood; lower = more anomalous
                raw_score = float(self.model.score_samples(feature_array)[0])

                # Normalise to 0-1 confidence (higher = more likely threat)
                # Typical raw scores range from -0.7 (normal) to -0.2 (anomaly)
                confidence = max(0.0, min(1.0, 1.0 - (raw_score + 0.5)))

                return {
                    "confidence": round(confidence, 4),
                    "threat_type": "anomaly" if prediction == -1 else "benign",
                    "is_anomaly": prediction == -1,
                    "anomaly_score": round(raw_score, 4),
                }
            except Exception as e:
                logger.error("IsolationForest prediction failed: %s", e)

        # Fallback: simple z-score based anomaly check
        return self._heuristic_predict(features)

    def _heuristic_predict(self, features: list[float]) -> dict:
        """Statistical fallback when no model is loaded."""
        arr = np.array(features)
        mean = np.mean(arr)
        std = np.std(arr) if np.std(arr) > 0 else 1.0
        z_scores = np.abs((arr - mean) / std)
        max_z = float(np.max(z_scores))

        # Higher z-score = more anomalous
        confidence = min(max_z / 5.0, 0.95)  # Cap at 0.95

        return {
            "confidence": round(confidence, 4),
            "threat_type": "anomaly" if confidence > 0.5 else "benign",
            "is_anomaly": confidence > 0.5,
            "anomaly_score": round(-confidence, 4),
        }

    @property
    def is_loaded(self) -> bool:
        return self.model is not None
