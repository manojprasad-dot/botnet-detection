"""
KOVIRX Endpoint Agent — Risk Engine.

Computes consolidated threat risk score by combining ML predictions,
anomaly detection, behavioral analysis, and threat intelligence.

Scoring Sources:
    ML Score (XGBoost + Isolation Forest): 40%
    Threat Intelligence (IOC match):      25%
    Behavior Score:                        25%
    Historical Score:                      10%
"""

import logging

logger = logging.getLogger("kovirx.agent.risk_engine")


class RiskEngine:
    """
    Multi-source risk score calculator.

    Aggregates signals from ML models, IOC databases, behavior analysis,
    and historical patterns into a single 0-100 risk score.
    """

    # Default weights — configurable per deployment
    WEIGHT_ML = 0.40
    WEIGHT_IOC = 0.25
    WEIGHT_BEHAVIOR = 0.25
    WEIGHT_HISTORY = 0.10

    def __init__(self):
        pass

    def calculate_risk(
        self,
        xgb_score: float,
        is_anomaly: bool,
        intel_score: float,
        behavior_score: float = 0.0,
        history_score: float = 0.0,
        features: dict[str, float] | None = None,
    ) -> dict:
        """
        Compute multi-source risk score.

        Args:
            xgb_score: XGBoost classification probability (0.0-1.0)
            is_anomaly: Isolation Forest anomaly flag
            intel_score: IOC/threat intel match score (0.0-1.0)
            behavior_score: Behavior analysis score (0.0-1.0)
            history_score: Historical device risk score (0.0-1.0)
            features: Optional feature dict for behavior signal extraction

        Returns:
            Dict with risk_score, severity, recommendation, and source breakdown.
        """
        # ── ML Score: combine XGBoost + Isolation Forest ──────────
        anomaly_boost = 0.8 if is_anomaly else 0.0
        ml_combined = max(xgb_score, anomaly_boost)

        # ── Extract behavior signals from features if available ───
        if behavior_score == 0.0 and features:
            behavior_score = self._extract_behavior_signals(features)

        # ── Weighted aggregation ──────────────────────────────────
        weighted_score = (
            (ml_combined * self.WEIGHT_ML)
            + (intel_score * self.WEIGHT_IOC)
            + (behavior_score * self.WEIGHT_BEHAVIOR)
            + (history_score * self.WEIGHT_HISTORY)
        )

        risk_score = int(round(weighted_score * 100))
        risk_score = min(100, max(0, risk_score))

        # ── Severity classification ───────────────────────────────
        if risk_score >= 85:
            severity = "critical"
            recommendation = (
                "Quarantine endpoint immediately. Block outbound traffic to "
                "destination IP. Initiate forensic investigation."
            )
        elif risk_score >= 60:
            severity = "high"
            recommendation = (
                "Trigger security investigation. Review system processes, "
                "check C2 indicators, and monitor network connections."
            )
        elif risk_score >= 35:
            severity = "medium"
            recommendation = (
                "Enable active telemetry collection. Monitor DNS queries "
                "and trace destination IPs. Review connection patterns."
            )
        else:
            severity = "low"
            recommendation = (
                "No action required. Telemetry metrics within standard "
                "operational baseline."
            )

        return {
            "risk_score": risk_score,
            "severity": severity,
            "recommendation": recommendation,
            "behavior_score": round(behavior_score, 4),
            "intel_score": round(intel_score, 4),
            "source_breakdown": {
                "ml_score": round(ml_combined, 4),
                "ml_contribution": round(ml_combined * self.WEIGHT_ML * 100, 1),
                "ioc_score": round(intel_score, 4),
                "ioc_contribution": round(intel_score * self.WEIGHT_IOC * 100, 1),
                "behavior_score": round(behavior_score, 4),
                "behavior_contribution": round(behavior_score * self.WEIGHT_BEHAVIOR * 100, 1),
                "history_score": round(history_score, 4),
                "history_contribution": round(history_score * self.WEIGHT_HISTORY * 100, 1),
            },
        }

    def _extract_behavior_signals(self, features: dict[str, float]) -> float:
        """
        Extract behavior risk signals from feature vector.

        Looks for: beacon patterns, DNS abuse, port scanning, high outbound rate.
        """
        signals = 0
        total_weight = 0.0

        # DNS beaconing / DGA
        dns_entropy = features.get("max_dns_entropy", 0.0)
        if dns_entropy >= 4.0:
            signals += 1
            total_weight += min(1.0, dns_entropy / 5.0)

        # Beacon regularity
        beacon = features.get("beacon_interval_score", 0.0)
        if beacon >= 0.7:
            signals += 1
            total_weight += beacon

        # Port scanning indicator
        failed_ratio = features.get("failed_connection_ratio", 0.0)
        if failed_ratio >= 0.5:
            signals += 1
            total_weight += failed_ratio

        # High packet rate (potential DDoS/scan)
        packet_rate = features.get("packet_rate", 0.0)
        if packet_rate >= 300.0:
            signals += 1
            total_weight += min(1.0, packet_rate / 500.0)

        # Suspicious TCP flags (RST floods)
        tcp_flag = features.get("tcp_flag_score", 0.0)
        if tcp_flag >= 0.5:
            signals += 1
            total_weight += tcp_flag

        if signals == 0:
            return 0.0

        return min(1.0, total_weight / max(1, signals))
