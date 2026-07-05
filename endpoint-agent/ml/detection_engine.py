"""
KOVIRX Endpoint Agent — Local ML Detection Engine.

Runs trained XGBoost + Isolation Forest models locally for real-time
threat classification without backend dependency.
"""

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger("kovirx.agent.ml.detection_engine")


class LocalDetectionEngine:
    """
    Executes trained ML models locally on the endpoint agent.

    Pipeline: Features → Normalize → SelectKBest → XGBoost → Isolation Forest → Classification
    Falls back to calibrated heuristic rules if model artifacts are unavailable.
    """

    FEATURE_NAMES = [
        # ── Legacy 22 features (Must remain first/same order) ──
        "event_count", "network_event_count", "dns_query_count", "max_dns_entropy",
        "avg_dns_entropy", "flow_duration", "packet_rate", "connection_count",
        "bytes_sent", "bytes_recv", "packets_sent", "packets_recv", "unique_remote_ips",
        "public_remote_ips", "listening_ports", "top_remote_port_count",
        "failed_connection_ratio", "tcp_flag_score", "beacon_interval_score",
        "outbound_frequency", "cpu_percent", "process_count",
        # ── Enterprise EDR 24 new features (Total 46) ──
        "min_packet_size", "max_packet_size", "mean_packet_size", "std_packet_size",
        "variance_packet_size", "byte_rate", "direction_ratio", "tcp_flags_syn_count",
        "tcp_flags_ack_count", "tcp_flags_fin_count", "tcp_flags_rst_count", "tcp_flags_psh_count",
        "tls_sni_entropy", "http_methods_get_count", "http_methods_post_count", "port_diversity",
        "session_duration", "payload_entropy", "connection_frequency", "beacon_interval_variance",
        "burst_count", "ram_percent", "disk_percent", "unique_dest_count"
    ]

    def __init__(self, model_dir: Path | str | None = None):
        if model_dir:
            self.model_dir = Path(model_dir)
        else:
            # Auto-detect: look for ai-engine/saved_models or ml/saved_models
            project_root = Path(__file__).resolve().parents[2]
            candidates = [
                project_root / "ai-engine" / "saved_models",
                project_root / "ml" / "saved_models",
            ]
            self.model_dir = next(
                (c for c in candidates if c.exists()), candidates[0]
            )

        self.xgboost_model = None
        self.isolation_model = None
        self.scaler = None
        self.selector = None
        self.loaded = False

    def load_models(self) -> bool:
        """Load pickled ML model artifacts from disk."""
        import joblib

        required = {
            "xgboost": self.model_dir / "xgboost_model.joblib",
            "isolation": self.model_dir / "isolation_forest.joblib",
            "scaler": self.model_dir / "scaler.joblib",
            "selector": self.model_dir / "feature_selector.joblib",
        }

        if not all(path.exists() for path in required.values()):
            logger.warning(
                "ML model artifacts not found in %s. Using heuristic fallback.",
                self.model_dir,
            )
            return False

        try:
            self.xgboost_model = joblib.load(required["xgboost"])
            self.isolation_model = joblib.load(required["isolation"])
            self.scaler = joblib.load(required["scaler"])
            self.selector = joblib.load(required["selector"])
            self.loaded = True
            logger.info("ML Detection Engine loaded from %s", self.model_dir)
            return True
        except Exception as e:
            logger.error("Failed to load ML models: %s", e)
            self.loaded = False
            return False

    def predict(self, features: dict[str, float]) -> dict:
        """
        Run local ML prediction on a feature vector.

        Returns:
            Dict with xgb_score, is_anomaly, threat_type
        """
        if not self.loaded:
            return self._heuristic_fallback(features)

        try:
            n_features = self.scaler.n_features_in_ if hasattr(self.scaler, "n_features_in_") else 22
            ordered = [float(features.get(name, 0.0)) for name in self.FEATURE_NAMES[:n_features]]
            ordered_arr = np.array([ordered])

            scaled = self.scaler.transform(ordered_arr)
            selected = self.selector.transform(scaled)

            xgb_proba = float(self.xgboost_model.predict_proba(selected)[0][1])
            anomaly_label = int(self.isolation_model.predict(selected)[0])
            is_anomaly = anomaly_label == -1

            threat_type = self._classify_threat(xgb_proba, is_anomaly, features)

            return {
                "xgb_score": xgb_proba,
                "is_anomaly": is_anomaly,
                "threat_type": threat_type,
            }
        except Exception as e:
            logger.error("ML prediction error: %s", e)
            return self._heuristic_fallback(features)

    def _classify_threat(
        self, xgb_score: float, is_anomaly: bool, features: dict[str, float]
    ) -> str:
        """Classify threat type based on ML scores and feature analysis."""
        if xgb_score >= 0.75:
            if features.get("beacon_interval_score", 0.0) >= 0.75:
                return "Beaconing"
            elif features.get("max_dns_entropy", 0.0) >= 4.0:
                return "DNS Abuse"
            elif features.get("failed_connection_ratio", 0.0) >= 0.5:
                return "Port Scan"
            else:
                return "Command & Control"
        elif is_anomaly:
            return "Unknown Threat"
        return "Normal"

    def _heuristic_fallback(self, features: dict[str, float]) -> dict:
        """Calibrated fallback when ML artifacts are unavailable."""
        dns_abuse = features.get("max_dns_entropy", 0.0) >= 4.2
        beaconing = features.get("beacon_interval_score", 0.0) >= 0.8
        port_scan = features.get("failed_connection_ratio", 0.0) >= 0.6
        c2 = (
            features.get("outbound_frequency", 0.0) >= 0.5
            and features.get("connection_count", 0) >= 100
        )

        xgb_score = 0.0
        threat_type = "Normal"

        if dns_abuse:
            xgb_score, threat_type = 0.85, "DNS Abuse"
        elif beaconing:
            xgb_score, threat_type = 0.88, "Beaconing"
        elif port_scan:
            xgb_score, threat_type = 0.78, "Port Scan"
        elif c2:
            xgb_score, threat_type = 0.92, "Command & Control"

        is_anomaly = features.get("unique_remote_ips", 0.0) >= 80.0
        if threat_type == "Normal" and is_anomaly:
            threat_type = "Unknown Threat"

        return {
            "xgb_score": xgb_score,
            "is_anomaly": is_anomaly,
            "threat_type": threat_type,
        }
