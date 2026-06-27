import logging

logger = logging.getLogger("kovirx.agent.services.risk_engine")


class RiskEngine:
    """
    Computes consolidated threat risk score by combining machine learning outputs,
    unsupervised anomaly tags, behavioral features, and threat intelligence matches.
    """

    def __init__(self):
        pass

    def calculate_risk(
        self,
        xgb_score: float,
        is_anomaly: bool,
        intel_score: float,
        features: dict[str, float],
    ) -> dict:
        """
        Consolidates metrics into a single threat risk score (0-100).
        Returns:
            - risk_score: int (0 to 100)
            - severity: str (low, medium, high, critical)
            - recommendation: str
        """
        # Base weight distribution
        # ML Prediction (XGBoost): 40%
        # Anomaly Detection (Isolation Forest): 20%
        # Threat Intel Match: 30%
        # Behavior Score: 10%

        anomaly_score = 0.8 if is_anomaly else 0.0

        # Calculate behavior score based on suspicious feature signals
        behavior_signals = 0
        if features.get("beacon_interval_score", 0.0) >= 0.7:
            behavior_signals += 1
        if features.get("max_dns_entropy", 0.0) >= 4.0:
            behavior_signals += 1
        if features.get("failed_connection_ratio", 0.0) >= 0.5:
            behavior_signals += 1
        if features.get("packet_rate", 0.0) >= 300.0:
            behavior_signals += 1

        behavior_score = min(1.0, behavior_signals * 0.25)

        weighted_score = (
            (xgb_score * 0.40)
            + (anomaly_score * 0.20)
            + (intel_score * 0.30)
            + (behavior_score * 0.10)
        )

        risk_score = int(round(weighted_score * 100))
        # Ensure ceiling bounds
        risk_score = min(100, max(0, risk_score))

        # Severity categorization
        if risk_score >= 85:
            severity = "critical"
            recommendation = "Quarantine endpoint node immediately and block outbound destination network traffic."
        elif risk_score >= 60:
            severity = "high"
            recommendation = "Trigger immediate security investigation, review system processes and check C2 network descriptors."
        elif risk_score >= 35:
            severity = "medium"
            recommendation = "Enable active telemetry collection, monitor DNS query rates, and trace destination IPs."
        else:
            severity = "low"
            recommendation = "No action required. Telemetry metrics remain within the standard operational baseline."

        return {
            "risk_score": risk_score,
            "severity": severity,
            "recommendation": recommendation,
        }
