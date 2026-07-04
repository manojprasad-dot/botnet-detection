"""
KOVIRX AI Engine — Feature Importance Analysis.

Generates feature importance rankings and per-prediction contributions
for the AI Explainability dashboard widget.
"""

import logging
import numpy as np

logger = logging.getLogger("kovirx.ai.feature_importance")


FEATURE_DISPLAY_NAMES = {
    "event_count": "Event Count",
    "network_event_count": "Network Events",
    "dns_query_count": "DNS Query Count",
    "max_dns_entropy": "Max DNS Entropy",
    "avg_dns_entropy": "Avg DNS Entropy",
    "flow_duration": "Flow Duration",
    "packet_rate": "Packet Rate",
    "connection_count": "Connection Count",
    "bytes_sent": "Bytes Sent",
    "bytes_recv": "Bytes Received",
    "packets_sent": "Packets Sent",
    "packets_recv": "Packets Received",
    "unique_remote_ips": "Unique Remote IPs",
    "public_remote_ips": "Public Remote IPs",
    "listening_ports": "Listening Ports",
    "top_remote_port_count": "Top Port Count",
    "failed_connection_ratio": "Failed Conn. Ratio",
    "tcp_flag_score": "TCP Flag Score",
    "beacon_interval_score": "Beacon Score",
    "outbound_frequency": "Outbound Frequency",
    "cpu_percent": "CPU Utilization",
    "process_count": "Process Count",
}


def compute_feature_importance(
    model,
    feature_names: list[str],
    top_n: int = 10,
) -> list[dict]:
    """
    Extract global feature importance from a trained model.

    Args:
        model: Trained sklearn/xgboost model with feature_importances_
        feature_names: Ordered list of feature names
        top_n: Number of top features to return

    Returns:
        Sorted list of {feature, display_name, importance} dicts
    """
    try:
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]

        result = []
        for idx in indices:
            name = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
            result.append({
                "feature": name,
                "display_name": FEATURE_DISPLAY_NAMES.get(name, name),
                "importance": round(float(importances[idx]), 6),
            })
        return result
    except Exception as e:
        logger.error("Feature importance extraction failed: %s", e)
        return []


def compute_prediction_explanation(
    features: dict[str, float],
    prediction_score: float,
    feature_names: list[str],
) -> dict:
    """
    Generate a per-prediction explanation using feature magnitude analysis.

    Falls back to magnitude-based importance when SHAP is unavailable.
    Used by the AI Explainability dashboard widget.
    """
    if not features:
        return {"contributions": {}, "method": "empty"}

    values = np.array([float(features.get(name, 0.0)) for name in feature_names])
    total = np.sum(np.abs(values))
    if total == 0:
        total = 1.0

    contributions = {}
    for i, name in enumerate(feature_names):
        contribution = values[i] / total
        if abs(contribution) > 0.01:  # Only include significant contributions
            contributions[name] = {
                "display_name": FEATURE_DISPLAY_NAMES.get(name, name),
                "value": round(float(values[i]), 4),
                "contribution": round(float(contribution), 6),
                "direction": "positive" if contribution > 0 else "negative",
            }

    # Sort by absolute contribution
    sorted_contributions = dict(
        sorted(contributions.items(), key=lambda x: abs(x[1]["contribution"]), reverse=True)
    )

    return {
        "prediction_score": round(prediction_score, 4),
        "method": "magnitude_analysis",
        "top_contributors": dict(list(sorted_contributions.items())[:8]),
        "total_features_analyzed": len(feature_names),
    }
