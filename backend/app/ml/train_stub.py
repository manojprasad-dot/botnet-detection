"""
KOVIRX — Synthetic data model trainer (development only).

Generates realistic synthetic network flow features and trains
both XGBoost and Isolation Forest models for demonstration.

Run: python -m app.ml.train_stub
"""

import logging
import os

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier

logger = logging.getLogger("kovirx.ml.train")

SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
FEATURE_NAMES = [
    "packet_rate", "beacon_interval", "dns_entropy", "flow_duration",
    "tcp_flags_encoded", "avg_packet_size", "failed_connections", "outbound_ratio",
]


def generate_synthetic_data(n_samples: int = 2000, botnet_ratio: float = 0.3):
    """
    Generate synthetic feature vectors with realistic distributions.

    Benign traffic: low packet rates, high entropy variance, few failures.
    Botnet traffic: high packet rates, regular beacon intervals, DGA domains.
    """
    rng = np.random.default_rng(42)
    n_botnet = int(n_samples * botnet_ratio)
    n_benign = n_samples - n_botnet

    # Benign traffic features
    benign = np.column_stack([
        rng.exponential(20, n_benign),           # packet_rate (low)
        rng.exponential(30, n_benign),           # beacon_interval std (high, irregular)
        rng.uniform(1.0, 3.5, n_benign),         # dns_entropy (normal domains)
        rng.exponential(5, n_benign),            # flow_duration
        rng.choice([2, 3, 6, 18], n_benign),     # tcp_flags (SYN+ACK combos)
        rng.uniform(100, 1500, n_benign),        # avg_packet_size
        rng.poisson(0.5, n_benign),              # failed_connections (rare)
        rng.uniform(0.1, 0.5, n_benign),         # outbound_ratio (balanced)
    ])

    # Botnet traffic features
    botnet = np.column_stack([
        rng.uniform(80, 500, n_botnet),          # packet_rate (high, flooding)
        rng.uniform(0.1, 2.0, n_botnet),         # beacon_interval std (regular = C2)
        rng.uniform(3.8, 5.5, n_botnet),         # dns_entropy (DGA domains)
        rng.uniform(0.01, 1.0, n_botnet),        # flow_duration (short bursts)
        rng.choice([1, 8, 9, 24], n_botnet),     # tcp_flags (SYN scans, RST)
        rng.uniform(40, 200, n_botnet),          # avg_packet_size (small packets)
        rng.poisson(5, n_botnet),                # failed_connections (many)
        rng.uniform(0.7, 1.0, n_botnet),         # outbound_ratio (mostly outbound)
    ])

    X = np.vstack([benign, botnet])
    y = np.concatenate([np.zeros(n_benign), np.ones(n_botnet)])

    # Shuffle
    idx = rng.permutation(n_samples)
    return X[idx], y[idx]


def train_models():
    """Train both models on synthetic data and save to disk."""
    os.makedirs(SAVE_DIR, exist_ok=True)

    X, y = generate_synthetic_data(n_samples=5000)
    logger.info("Generated %d synthetic samples (%.0f%% botnet)", len(y), y.mean() * 100)

    # ── XGBoost ────────────────────────────────────────────────
    xgb = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
    )
    xgb.fit(X, y)
    xgb_path = os.path.join(SAVE_DIR, "xgboost_model.pkl")
    joblib.dump(xgb, xgb_path)
    logger.info("XGBoost model saved to %s", xgb_path)

    # Quick accuracy check
    train_acc = float((xgb.predict(X) == y).mean())
    logger.info("XGBoost train accuracy: %.2f%%", train_acc * 100)

    # ── Isolation Forest ───────────────────────────────────────
    iforest = IsolationForest(
        n_estimators=100,
        contamination=0.3,
        random_state=42,
    )
    iforest.fit(X)
    iforest_path = os.path.join(SAVE_DIR, "isolation_forest.pkl")
    joblib.dump(iforest, iforest_path)
    logger.info("IsolationForest model saved to %s", iforest_path)

    print(f"\n✅ Models trained and saved to {SAVE_DIR}/")
    print(f"   XGBoost accuracy: {train_acc:.2%}")
    print(f"   Files: xgboost_model.pkl, isolation_forest.pkl")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_models()
