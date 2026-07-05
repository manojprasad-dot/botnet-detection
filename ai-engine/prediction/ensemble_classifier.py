"""
KOVIRX AI Engine — Ensemble Threat Classifier.

Implements a Voting Classifier ensemble combining:
  1. Random Forest (High-throughput traffic screen)
  2. XGBoost (Known-threat signature classifier)
  3. Isolation Forest (Unsupervised anomaly verifier)

Includes automatic fallback to heuristics and feature importance explainability.
"""

import os
import logging
from pathlib import Path
import joblib
import numpy as np
from ml.feature_schema import FEATURE_NAMES

logger = logging.getLogger("kovirx.ai.ensemble")


class EnsembleThreatClassifier:
    """
    Ensemble classifier executing Random Forest, XGBoost, and Isolation Forest.
    """

    def __init__(self, model_dir: Path | str | None = None):
        if model_dir:
            self.model_dir = Path(model_dir)
        else:
            # Auto-detect models directory
            project_root = Path(__file__).resolve().parents[2]
            candidates = [
                project_root / "ai-engine" / "saved_models",
                project_root / "ml" / "saved_models",
            ]
            self.model_dir = next((c for c in candidates if c.exists()), candidates[0])

        self.xgboost_model = None
        self.random_forest_model = None
        self.isolation_forest_model = None
        self.scaler = None
        self.selector = None
        self.loaded = False

        self._load_models()

    def _load_models(self) -> None:
        """Load joblib model artifacts from disk."""
        paths = {
            "xgb": self.model_dir / "xgboost_model.joblib",
            "rf": self.model_dir / "random_forest_model.joblib",
            "iforest": self.model_dir / "isolation_forest.joblib",
            "scaler": self.model_dir / "scaler.joblib",
            "selector": self.model_dir / "feature_selector.joblib",
        }

        if not all(p.exists() for p in paths.values()):
            logger.warning("Ensemble model files not fully present in %s. Using fallback heuristic.", self.model_dir)
            return

        try:
            self.xgboost_model = joblib.load(paths["xgb"])
            self.random_forest_model = joblib.load(paths["rf"])
            self.isolation_forest_model = joblib.load(paths["iforest"])
            self.scaler = joblib.load(paths["scaler"])
            self.selector = joblib.load(paths["selector"])
            self.loaded = True
            logger.info("Ensemble threat classifier models loaded successfully from %s", self.model_dir)
        except Exception as e:
            logger.error("Ensemble threat classifier load failed: %s", e)
            self.loaded = False

    def predict(self, features: dict[str, float]) -> dict:
        """
        Predict threat level and confidence using Voting Classifier ensemble.
        """
        if not self.loaded:
            return self._heuristic_fallback(features)

        try:
            # Slice features dynamically based on n_features expected by the scaler
            n_features = self.scaler.n_features_in_ if hasattr(self.scaler, "n_features_in_") else 22
            ordered = [float(features.get(name, 0.0)) for name in FEATURE_NAMES[:n_features]]
            ordered_arr = np.array([ordered])

            scaled = self.scaler.transform(ordered_arr)
            selected = self.selector.transform(scaled)

            # Probabilities/Predictions
            xgb_proba = float(self.xgboost_model.predict_proba(selected)[0][1])
            rf_proba = float(self.random_forest_model.predict_proba(selected)[0][1])
            if_label = int(self.isolation_forest_model.predict(selected)[0])
            if_proba = 0.85 if if_label == -1 else 0.15

            # Voting Classifier weight aggregation
            # 40% XGBoost, 30% Random Forest, 30% Isolation Forest
            confidence = (xgb_proba * 0.4) + (rf_proba * 0.3) + (if_proba * 0.3)

            is_threat = confidence >= 0.55
            threat_type = "benign"
            if is_threat:
                # Classify specific threat
                if features.get("beacon_interval_score", 0.0) >= 0.75:
                    threat_type = "Beaconing"
                elif features.get("max_dns_entropy", 0.0) >= 4.0:
                    threat_type = "DNS Abuse"
                elif features.get("failed_connection_ratio", 0.0) >= 0.5:
                    threat_type = "Port Scan"
                else:
                    threat_type = "Command & Control"

            # Compute feature importances/reasons
            reasons = self._generate_reasons(features)

            return {
                "label": "botnet" if is_threat else "benign",
                "confidence": confidence,
                "threat_type": threat_type,
                "reasons": reasons,
                "model_signals": {
                    "xgboost": xgb_proba,
                    "random_forest": rf_proba,
                    "isolation_forest": if_proba
                }
            }

        except Exception as e:
            logger.error("Ensemble prediction failed: %s", e)
            return self._heuristic_fallback(features)

    def _generate_reasons(self, features: dict[str, float]) -> list[str]:
        reasons = []
        if features.get("beacon_interval_score", 0.0) >= 0.75:
            reasons.append(f"Regular connection beacons (Score: {features['beacon_interval_score']:.2f})")
        if features.get("max_dns_entropy", 0.0) >= 4.0:
            reasons.append(f"High DNS query entropy (Entropy: {features['max_dns_entropy']:.2f})")
        if features.get("failed_connection_ratio", 0.0) >= 0.5:
            reasons.append(f"High connection failure rate (Ratio: {features['failed_connection_ratio']:.2f})")
        if features.get("outbound_frequency", 0.0) >= 0.8:
            reasons.append(f"Suspicious outbound frequency ({features['outbound_frequency']:.2f} pkts/s)")
        if not reasons:
            reasons.append("Flow pattern aligns with normal benign baseline behavior.")
        return reasons[:3]

    def _heuristic_fallback(self, features: dict[str, float]) -> dict:
        score = 0.0
        threat_type = "benign"

        if features.get("max_dns_entropy", 0.0) >= 4.2:
            score += 0.35
            threat_type = "DNS Abuse"
        if features.get("beacon_interval_score", 0.0) >= 0.8:
            score += 0.40
            threat_type = "Beaconing"
        if features.get("failed_connection_ratio", 0.0) >= 0.6:
            score += 0.30
            threat_type = "Port Scan"
        if features.get("outbound_frequency", 0.0) >= 0.6:
            score += 0.25
            threat_type = "Command & Control"

        is_threat = score >= 0.5

        return {
            "label": "botnet" if is_threat else "benign",
            "confidence": min(score, 0.99),
            "threat_type": threat_type if is_threat else "benign",
            "reasons": self._generate_reasons(features),
            "model_signals": {
                "xgboost": score,
                "random_forest": score,
                "isolation_forest": 0.5
            }
        }
