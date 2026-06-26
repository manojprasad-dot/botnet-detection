"""
KOVIRX — XGBoost binary classifier wrapper.

Classifies network flows as botnet vs benign.
"""

import logging
import os

import joblib
import numpy as np

logger = logging.getLogger("kovirx.ml.xgboost")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "saved_models", "xgboost_model.pkl")


class XGBoostDetector:
    """Wrapper around an XGBoost binary classifier."""

    def __init__(self):
        self.model = None
        self.feature_names = [
            "packet_rate", "beacon_interval", "dns_entropy", "flow_duration",
            "tcp_flags_encoded", "avg_packet_size", "failed_connections", "outbound_ratio",
        ]
        self._load_model()

    def _load_model(self) -> None:
        """Load a pre-trained model from disk."""
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                logger.info("XGBoost model loaded from %s", MODEL_PATH)
            except Exception as e:
                logger.warning("Failed to load XGBoost model: %s", e)
                self.model = None
        else:
            logger.info("No pre-trained XGBoost model found, using fallback heuristic")

    def predict(self, features: list[float]) -> dict:
        """
        Run inference on a feature vector.

        Returns:
            dict with 'confidence', 'threat_type', 'is_threat', 'probabilities'
        """
        feature_array = np.array(features).reshape(1, -1)

        if self.model is not None:
            try:
                proba = self.model.predict_proba(feature_array)[0]
                prediction = int(self.model.predict(feature_array)[0])
                confidence = float(proba[1])  # probability of botnet class

                return {
                    "confidence": confidence,
                    "threat_type": "botnet" if prediction == 1 else "benign",
                    "is_threat": prediction == 1,
                    "probabilities": {"benign": float(proba[0]), "botnet": float(proba[1])},
                }
            except Exception as e:
                logger.error("XGBoost prediction failed: %s", e)

        # Fallback heuristic when no model is loaded
        return self._heuristic_predict(features)

    def _heuristic_predict(self, features: list[float]) -> dict:
        """
        Rule-based fallback using feature thresholds.

        This runs when no trained model is available.
        """
        # features: [packet_rate, beacon_interval, dns_entropy, flow_duration,
        #            tcp_flags, avg_packet_size, failed_connections, outbound_ratio]
        score = 0.0

        if len(features) >= 8:
            # High packet rate indicates flooding
            if features[0] > 100:
                score += 0.25
            # Low beacon interval std = regular beaconing
            if 0 < features[1] < 2.0:
                score += 0.20
            # High DNS entropy = DGA domains
            if features[2] > 4.0:
                score += 0.25
            # Many failed connections
            if features[6] > 5:
                score += 0.15
            # High outbound ratio
            if features[7] > 0.8:
                score += 0.15

        return {
            "confidence": min(score, 0.99),
            "threat_type": "botnet" if score >= 0.5 else "benign",
            "is_threat": score >= 0.5,
            "probabilities": {"benign": 1 - score, "botnet": score},
        }

    @property
    def is_loaded(self) -> bool:
        return self.model is not None
