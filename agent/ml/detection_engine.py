import logging
import os
import joblib
from pathlib import Path
import numpy as np

logger = logging.getLogger("kovirx.agent.ml.detection_engine")


class LocalDetectionEngine:
    """
    Executes trained ML models (XGBoost + Isolation Forest) locally on the Endpoint Agent.
    Implements normalization and feature selection matching the backend training.
    """

    FEATURE_NAMES = [
        "event_count", "network_event_count", "dns_query_count", "max_dns_entropy",
        "avg_dns_entropy", "flow_duration", "packet_rate", "connection_count",
        "bytes_sent", "bytes_recv", "packets_sent", "packets_recv", "unique_remote_ips",
        "public_remote_ips", "listening_ports", "top_remote_port_count",
        "failed_connection_ratio", "tcp_flag_score", "beacon_interval_score",
        "outbound_frequency", "cpu_percent", "process_count"
    ]

    def __init__(self, model_dir: Path | str | None = None):
        if not model_dir:
            # Resolve to root ml/saved_models
            model_dir = Path(__file__).resolve().parents[3] / "ml" / "saved_models"
        else:
            model_dir = Path(model_dir)

        self.model_dir = model_dir
        self.xgboost_model = None
        self.isolation_model = None
        self.scaler = None
        self.selector = None
        self.loaded = False

    def load_models(self) -> bool:
        """Load pickled artifacts."""
        required = {
            "xgboost": self.model_dir / "xgboost_model.joblib",
            "isolation": self.model_dir / "isolation_forest.joblib",
            "scaler": self.model_dir / "scaler.joblib",
            "selector": self.model_dir / "feature_selector.joblib",
        }

        if not all(path.exists() for path in required.values()):
            logger.warning("Local models not found in %s. Local ML inference is disabled.", self.model_dir)
            return False

        try:
            self.xgboost_model = joblib.load(required["xgboost"])
            self.isolation_model = joblib.load(required["isolation"])
            self.scaler = joblib.load(required["scaler"])
            self.selector = joblib.load(required["selector"])
            self.loaded = True
            logger.info("Local ML Detection Engine loaded successfully from %s", self.model_dir)
            return True
        except Exception as e:
            logger.error("Failed to load local ML models: %s", e)
            self.loaded = False
            return False

    def predict(self, features: dict[str, float]) -> dict:
        """
        Run local ML prediction on features.
        Returns:
            - xgb_score: float (0.0 to 1.0)
            - is_anomaly: bool
            - threat_type: str
        """
        if not self.loaded:
            return self._heuristic_fallback(features)

        try:
            # Construct ordered feature vector matching FEATURE_NAMES
            ordered = [float(features.get(name, 0.0)) for name in self.FEATURE_NAMES]
            ordered_arr = np.array([ordered])

            # Preprocess
            scaled = self.scaler.transform(ordered_arr)
            selected = self.selector.transform(scaled)

            # Classify using XGBoost
            xgb_proba = float(self.xgboost_model.predict_proba(selected)[0][1])

            # Check anomaly using Isolation Forest
            anomaly_label = int(self.isolation_model.predict(selected)[0])
            is_anomaly = (anomaly_label == -1)

            # Determine classification label
            threat_type = "Normal"
            if xgb_proba >= 0.75:
                # Classify C2 vs beaconing vs scan using feature-based heuristics
                if features.get("beacon_interval_score", 0.0) >= 0.75:
                    threat_type = "Beaconing"
                elif features.get("max_dns_entropy", 0.0) >= 4.0:
                    threat_type = "DNS Abuse"
                elif features.get("failed_connection_ratio", 0.0) >= 0.5:
                    threat_type = "Port Scan"
                else:
                    threat_type = "Command & Control"
            elif is_anomaly:
                threat_type = "Unknown Threat"

            return {
                "xgb_score": xgb_proba,
                "is_anomaly": is_anomaly,
                "threat_type": threat_type,
                "features_used": features,
            }
        except Exception as e:
            logger.error("Error running local ML prediction: %s", e)
            return self._heuristic_fallback(features)

    def _heuristic_fallback(self, features: dict[str, float]) -> dict:
        """Calibrated fallback logic when ML artifacts are missing or fail."""
        # Simple threat rule proxy
        dns_abuse = features.get("max_dns_entropy", 0.0) >= 4.2
        beaconing = features.get("beacon_interval_score", 0.0) >= 0.8
        port_scan = features.get("failed_connection_ratio", 0.0) >= 0.6
        c2 = (features.get("outbound_frequency", 0.0) >= 0.5) and (features.get("connection_count", 0) >= 100)

        xgb_score = 0.0
        threat_type = "Normal"

        if dns_abuse:
            xgb_score = 0.85
            threat_type = "DNS Abuse"
        elif beaconing:
            xgb_score = 0.88
            threat_type = "Beaconing"
        elif port_scan:
            xgb_score = 0.78
            threat_type = "Port Scan"
        elif c2:
            xgb_score = 0.92
            threat_type = "Command & Control"

        is_anomaly = features.get("unique_remote_ips", 0.0) >= 80.0

        if threat_type == "Normal" and is_anomaly:
            threat_type = "Unknown Threat"

        return {
            "xgb_score": xgb_score,
            "is_anomaly": is_anomaly,
            "threat_type": threat_type,
            "features_used": features,
        }
