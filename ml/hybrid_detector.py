from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.core.config import settings
from backend.schemas.telemetry import Severity, TelemetryBatch
from ml.feature_extractor import extract_feature_vector, feature_vector_to_ordered_list
from ml.feature_schema import MODEL_LAYERS


@dataclass
class ModelSignal:
    layer: str
    score: float
    label: str
    explanation: str


@dataclass
class HybridPrediction:
    label: str
    severity: Severity
    confidence_score: float
    risk_score: int
    model_mode: str
    signals: list[ModelSignal] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)
    features: dict[str, float] = field(default_factory=dict)

    @property
    def is_threat(self) -> bool:
        return self.label != "benign" and self.risk_score >= 55


class HybridThreatDetector:
    def __init__(self, artifact_dir: str | None = None) -> None:
        configured_dir = Path(artifact_dir or settings.model_artifact_dir)
        if configured_dir.is_absolute():
            self.artifact_dir = configured_dir
        else:
            self.artifact_dir = Path(__file__).resolve().parents[2] / configured_dir
        self._artifacts_loaded = False
        self._xgboost_model: Any | None = None
        self._random_forest_model: Any | None = None
        self._isolation_model: Any | None = None
        self._scaler: Any | None = None
        self._selector: Any | None = None

    def predict(self, batch: TelemetryBatch) -> HybridPrediction:
        features = extract_feature_vector(batch)
        if self._load_artifacts_once():
            return self._predict_with_artifacts(features)

        return self._predict_with_calibrated_rules(features)

    def get_pipeline_status(self) -> dict[str, Any]:
        artifact_files = {
            "xgboost": self.artifact_dir / "xgboost_model.joblib",
            "random_forest": self.artifact_dir / "random_forest_model.joblib",
            "isolation_forest": self.artifact_dir / "isolation_forest.joblib",
            "scaler": self.artifact_dir / "scaler.joblib",
            "selector": self.artifact_dir / "feature_selector.joblib",
        }
        available = {
            key: path.exists()
            for key, path in artifact_files.items()
        }
        return {
            "model_mode": "trained-artifacts" if all(available.values()) else "calibrated-fallback",
            "artifact_dir": str(self.artifact_dir),
            "available_artifacts": available,
            "pipeline_layers": MODEL_LAYERS,
            "primary_model": "Ensemble Voting Classifier (XGBoost + Random Forest)",
            "anomaly_model": "Isolation Forest",
            "explainability": "SHAP-ready training pipeline; runtime fallback uses feature attribution rules",
        }

    def _load_artifacts_once(self) -> bool:
        if self._artifacts_loaded:
            return all((self._xgboost_model, self._isolation_model, self._scaler, self._selector))

        self._artifacts_loaded = True
        required_paths = {
            "xgboost": self.artifact_dir / "xgboost_model.joblib",
            "isolation": self.artifact_dir / "isolation_forest.joblib",
            "scaler": self.artifact_dir / "scaler.joblib",
            "selector": self.artifact_dir / "feature_selector.joblib",
        }
        rf_path = self.artifact_dir / "random_forest_model.joblib"

        if not all(path.exists() for path in required_paths.values()):
            return False

        try:
            import joblib

            self._xgboost_model = joblib.load(required_paths["xgboost"])
            self._isolation_model = joblib.load(required_paths["isolation"])
            self._scaler = joblib.load(required_paths["scaler"])
            self._selector = joblib.load(required_paths["selector"])
            if rf_path.exists():
                self._random_forest_model = joblib.load(rf_path)
        except Exception:
            self._xgboost_model = None
            self._isolation_model = None
            self._scaler = None
            self._selector = None
            self._random_forest_model = None
            return False

        return True

    def _predict_with_artifacts(self, features: dict[str, float]) -> HybridPrediction:
        from ml.feature_schema import FEATURE_NAMES
        n_features = self._scaler.n_features_in_ if hasattr(self._scaler, "n_features_in_") else 22
        ordered = [[float(features.get(name, 0.0)) for name in FEATURE_NAMES[:n_features]]]
        transformed = self._scaler.transform(ordered)
        selected = self._selector.transform(transformed)

        xgb_probability = float(self._xgboost_model.predict_proba(selected)[0][1])
        
        # Calculate Random Forest probability if available, otherwise fallback to XGBoost
        if self._random_forest_model is not None:
            rf_probability = float(self._random_forest_model.predict_proba(selected)[0][1])
        else:
            rf_probability = xgb_probability

        anomaly_label = int(self._isolation_model.predict(selected)[0])
        anomaly_score = 0.85 if anomaly_label == -1 else 0.15

        # Voting Classifier aggregated risk score
        # 40% XGBoost, 30% Random Forest, 30% Isolation Forest
        risk_score = int(min(100, ((xgb_probability * 0.4) + (rf_probability * 0.3) + (anomaly_score * 0.3)) * 100))
        severity = severity_from_risk(risk_score)
        label = "botnet" if risk_score >= 55 else "benign"

        signals = [
            ModelSignal(
                layer="Random Forest fast screen",
                score=rf_probability,
                label="botnet" if rf_probability >= 0.5 else "benign",
                explanation="Fast tree classifier screening for malicious network patterns.",
            ),
            ModelSignal(
                layer="XGBoost known-threat classifier",
                score=xgb_probability,
                label="botnet" if xgb_probability >= 0.5 else "benign",
                explanation="Classifies known botnet-like tabular traffic patterns.",
            ),
            ModelSignal(
                layer="Isolation Forest unknown-threat verifier",
                score=anomaly_score,
                label="anomaly" if anomaly_label == -1 else "normal",
                explanation="Checks whether the feature vector deviates from trained benign behavior.",
            ),
        ]

        return HybridPrediction(
            label=label,
            severity=severity,
            confidence_score=min(0.99, max(xgb_probability, rf_probability, anomaly_score)),
            risk_score=risk_score,
            model_mode="trained-artifacts",
            signals=signals,
            explanations=build_feature_explanations(features),
            features=features,
        )

    def _predict_with_calibrated_rules(self, features: dict[str, float]) -> HybridPrediction:
        fast_score = min(1.0, features["connection_count"] / 250)
        xgb_proxy_score = min(
            1.0,
            (
            features["max_dns_entropy"] / 6.0 * 0.34
            + features["public_remote_ips"] / 45.0 * 0.30
            + features["beacon_interval_score"] * 0.22
            + features["packet_rate"] / 120.0 * 0.10
            + features["failed_connection_ratio"] * 0.14
        ),
        )
        isolation_proxy_score = min(
            1.0,
            (
                features["unique_remote_ips"] / 55.0 * 0.45
                + features["outbound_frequency"] / 80.0 * 0.35
                + features["tcp_flag_score"] * 0.20
                + features["flow_duration"] / 600.0 * 0.08
            ),
        )
        risk_score = int(
            min(
                100,
                fast_score * 24
                + xgb_proxy_score * 48
                + isolation_proxy_score * 28,
            )
        )
        severity = severity_from_risk(risk_score)
        label = "botnet" if risk_score >= 55 else "benign"

        signals = [
            ModelSignal(
                layer="Random Forest fast screen",
                score=fast_score,
                label="suspicious" if fast_score >= 0.55 else "normal",
                explanation="Fast threshold-style screen over connection and packet volume.",
            ),
            ModelSignal(
                layer="XGBoost known-threat classifier",
                score=xgb_proxy_score,
                label="botnet-like" if xgb_proxy_score >= 0.5 else "benign-like",
                explanation="Calibrated proxy until a trained XGBoost artifact is available.",
            ),
            ModelSignal(
                layer="Isolation Forest unknown-threat verifier",
                score=isolation_proxy_score,
                label="anomaly" if isolation_proxy_score >= 0.5 else "normal",
                explanation="Calibrated anomaly proxy for unknown or rare behavior.",
            ),
        ]

        return HybridPrediction(
            label=label,
            severity=severity,
            confidence_score=min(0.98, max(0.48, risk_score / 100)),
            risk_score=risk_score,
            model_mode="calibrated-fallback",
            signals=signals,
            explanations=build_feature_explanations(features),
            features=features,
        )


def severity_from_risk(risk_score: int) -> Severity:
    if risk_score >= 90:
        return Severity.critical
    if risk_score >= 65:
        return Severity.high
    if risk_score >= 35:
        return Severity.medium
    return Severity.low


def build_feature_explanations(features: dict[str, float]) -> list[str]:
    candidates = [
        (
            features["max_dns_entropy"],
            f"DNS entropy peaked at {features['max_dns_entropy']:.2f}",
        ),
        (
            features["connection_count"] / 50,
            f"Connection volume reached {int(features['connection_count'])}",
        ),
        (
            features["public_remote_ips"] / 8,
            f"Public remote destinations reached {int(features['public_remote_ips'])}",
        ),
        (
            features["beacon_interval_score"] * 6,
            f"Beacon interval score is {features['beacon_interval_score']:.2f}",
        ),
        (
            features["outbound_frequency"] / 20,
            f"Outbound frequency is {features['outbound_frequency']:.2f}",
        ),
    ]
    ranked = sorted(candidates, key=lambda item: item[0], reverse=True)
    explanations = [text for score, text in ranked if score > 0][:4]
    if not explanations:
        explanations.append("Feature vector is close to the current benign baseline")
    return explanations


hybrid_detector = HybridThreatDetector()
