"""
KOVIRX — SHAP Explainability module.

Generates per-feature contribution explanations for XGBoost predictions.
"""

import logging

import numpy as np

logger = logging.getLogger("kovirx.ml.explainer")

FEATURE_NAMES = [
    "packet_rate", "beacon_interval", "dns_entropy", "flow_duration",
    "tcp_flags_encoded", "avg_packet_size", "failed_connections", "outbound_ratio",
]


def explain_prediction(model, features: list[float]) -> dict | None:
    """
    Generate SHAP feature-importance explanation for a prediction.

    Falls back to a permutation-based approximation if SHAP is unavailable.
    """
    if model is None:
        return _fallback_explanation(features)

    try:
        import shap

        feature_array = np.array(features).reshape(1, -1)
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(feature_array)

        # For binary classification, shap_values may be a list [class_0, class_1]
        if isinstance(shap_values, list):
            values = shap_values[1][0]  # class 1 (botnet) contributions
        else:
            values = shap_values[0]

        explanation = {
            "feature_contributions": {
                name: round(float(val), 6)
                for name, val in zip(FEATURE_NAMES, values)
            },
            "base_value": round(float(explainer.expected_value[1]
                                     if isinstance(explainer.expected_value, (list, np.ndarray))
                                     else explainer.expected_value), 6),
            "method": "shap_tree",
        }
        return explanation

    except ImportError:
        logger.warning("SHAP not installed, using fallback explanation")
        return _fallback_explanation(features)
    except Exception as e:
        logger.error("SHAP explanation failed: %s", e)
        return _fallback_explanation(features)


def _fallback_explanation(features: list[float]) -> dict:
    """
    Simple feature-magnitude-based explanation when SHAP is unavailable.

    Uses normalised feature values as proxy importance scores.
    """
    if not features:
        return {"feature_contributions": {}, "method": "fallback"}

    arr = np.array(features)
    total = np.sum(np.abs(arr)) if np.sum(np.abs(arr)) > 0 else 1.0
    contributions = arr / total

    return {
        "feature_contributions": {
            name: round(float(val), 6)
            for name, val in zip(FEATURE_NAMES, contributions)
        },
        "base_value": 0.0,
        "method": "fallback_magnitude",
    }
