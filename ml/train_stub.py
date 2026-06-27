"""
KOVIRX — Model Trainer for Development & Startup seeding.

Generates realistic synthetic data for both the 8-feature legacy stub
and the 23-feature hybrid enterprise pipeline, training and exporting all models.
"""

import logging
import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

logger = logging.getLogger("kovirx.ml.train")

SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved_models")

# ── Legacy 8-Feature Definitions ───────────────────────────────────
LEGACY_FEATURE_NAMES = [
    "packet_rate", "beacon_interval", "dns_entropy", "flow_duration",
    "tcp_flags_encoded", "avg_packet_size", "failed_connections", "outbound_ratio",
]

# ── Hybrid 23-Feature Definitions ──────────────────────────────────
HYBRID_FEATURE_NAMES = [
    "event_count", "network_event_count", "dns_query_count", "max_dns_entropy",
    "avg_dns_entropy", "flow_duration", "packet_rate", "connection_count",
    "bytes_sent", "bytes_recv", "packets_sent", "packets_recv", "unique_remote_ips",
    "public_remote_ips", "listening_ports", "top_remote_port_count",
    "failed_connection_ratio", "tcp_flag_score", "beacon_interval_score",
    "outbound_frequency", "cpu_percent", "process_count"
]


def generate_legacy_synthetic_data(n_samples: int = 2000, botnet_ratio: float = 0.3):
    rng = np.random.default_rng(42)
    n_botnet = int(n_samples * botnet_ratio)
    n_benign = n_samples - n_botnet

    benign = np.column_stack([
        rng.exponential(20, n_benign),           # packet_rate (low)
        rng.exponential(30, n_benign),           # beacon_interval std (high)
        rng.uniform(1.0, 3.5, n_benign),         # dns_entropy
        rng.exponential(5, n_benign),            # flow_duration
        rng.choice([2, 3, 6, 18], n_benign),     # tcp_flags
        rng.uniform(100, 1500, n_benign),        # avg_packet_size
        rng.poisson(0.5, n_benign),              # failed_connections
        rng.uniform(0.1, 0.5, n_benign),         # outbound_ratio
    ])

    botnet = np.column_stack([
        rng.uniform(80, 500, n_botnet),          # packet_rate
        rng.uniform(0.1, 2.0, n_botnet),         # beacon_interval std
        rng.uniform(3.8, 5.5, n_botnet),         # dns_entropy
        rng.uniform(0.01, 1.0, n_botnet),        # flow_duration
        rng.choice([1, 8, 9, 24], n_botnet),     # tcp_flags
        rng.uniform(40, 200, n_botnet),          # avg_packet_size
        rng.poisson(5, n_botnet),                # failed_connections
        rng.uniform(0.7, 1.0, n_botnet),         # outbound_ratio
    ])

    X = np.vstack([benign, botnet])
    y = np.concatenate([np.zeros(n_benign), np.ones(n_botnet)])
    idx = rng.permutation(n_samples)
    return X[idx], y[idx]


def generate_hybrid_synthetic_data(n_samples: int = 5000, botnet_ratio: float = 0.3):
    rng = np.random.default_rng(42)
    n_botnet = int(n_samples * botnet_ratio)
    n_benign = n_samples - n_botnet

    # Benign data generation (23 features)
    benign = np.column_stack([
        rng.poisson(80, n_benign),               # event_count
        rng.poisson(50, n_benign),               # network_event_count
        rng.poisson(10, n_benign),               # dns_query_count
        rng.uniform(1.0, 3.2, n_benign),         # max_dns_entropy
        rng.uniform(1.0, 2.5, n_benign),         # avg_dns_entropy
        rng.exponential(45, n_benign),           # flow_duration
        rng.exponential(12, n_benign),           # packet_rate
        rng.poisson(30, n_benign),               # connection_count
        rng.uniform(1000, 15000, n_benign),      # bytes_sent
        rng.uniform(2000, 30000, n_benign),      # bytes_recv
        rng.poisson(20, n_benign),               # packets_sent
        rng.poisson(35, n_benign),               # packets_recv
        rng.poisson(5, n_benign),                # unique_remote_ips
        rng.poisson(2, n_benign),                # public_remote_ips
        rng.poisson(3, n_benign),                # listening_ports
        rng.poisson(8, n_benign),                # top_remote_port_count
        rng.uniform(0.01, 0.08, n_benign),       # failed_connection_ratio
        rng.uniform(0.05, 0.20, n_benign),       # tcp_flag_score
        rng.uniform(0.02, 0.15, n_benign),       # beacon_interval_score
        rng.uniform(0.05, 0.30, n_benign),       # outbound_frequency
        rng.uniform(1.0, 15.0, n_benign),        # cpu_percent
        rng.poisson(60, n_benign),               # process_count
    ])

    # Botnet data generation (23 features)
    botnet = np.column_stack([
        rng.poisson(350, n_botnet),              # event_count
        rng.poisson(300, n_botnet),              # network_event_count
        rng.poisson(80, n_botnet),               # dns_query_count
        rng.uniform(3.8, 5.8, n_botnet),         # max_dns_entropy
        rng.uniform(3.0, 4.8, n_botnet),         # avg_dns_entropy
        rng.uniform(0.2, 8.0, n_botnet),         # flow_duration
        rng.uniform(120, 950, n_botnet),         # packet_rate
        rng.poisson(180, n_botnet),              # connection_count
        rng.uniform(15000, 85000, n_botnet),     # bytes_sent
        rng.uniform(3000, 12000, n_botnet),      # bytes_recv
        rng.poisson(150, n_botnet),              # packets_sent
        rng.poisson(60, n_botnet),               # packets_recv
        rng.poisson(45, n_botnet),               # unique_remote_ips
        rng.poisson(38, n_botnet),               # public_remote_ips
        rng.poisson(1, n_botnet),                # listening_ports
        rng.poisson(90, n_botnet),               # top_remote_port_count
        rng.uniform(0.65, 0.98, n_botnet),       # failed_connection_ratio
        rng.uniform(0.70, 1.0, n_botnet),        # tcp_flag_score
        rng.uniform(0.80, 1.0, n_botnet),        # beacon_interval_score
        rng.uniform(0.75, 1.0, n_botnet),        # outbound_frequency
        rng.uniform(40.0, 95.0, n_botnet),       # cpu_percent
        rng.poisson(120, n_botnet),              # process_count
    ])

    X = np.vstack([benign, botnet])
    y = np.concatenate([np.zeros(n_benign), np.ones(n_botnet)])
    idx = rng.permutation(n_samples)
    return X[idx], y[idx]


def train_models():
    """Train both legacy models and hybrid pipeline models."""
    os.makedirs(SAVE_DIR, exist_ok=True)

    # ── 1. Train Legacy 8-Feature Models ───────────────────────────
    logger.info("Training legacy 8-feature stub models...")
    X_leg, y_leg = generate_legacy_synthetic_data(n_samples=4000)

    # Legacy XGBoost
    xgb_leg = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        eval_metric="logloss",
        random_state=42,
    )
    xgb_leg.fit(X_leg, y_leg)
    joblib.dump(xgb_leg, os.path.join(SAVE_DIR, "xgboost_model.pkl"))

    # Legacy Isolation Forest
    if_leg = IsolationForest(
        n_estimators=100,
        contamination=0.3,
        random_state=42,
    )
    if_leg.fit(X_leg)
    joblib.dump(if_leg, os.path.join(SAVE_DIR, "isolation_forest.pkl"))
    logger.info("Legacy 8-feature stub models saved successfully.")

    # ── 2. Train Hybrid 23-Feature Models ──────────────────────────
    logger.info("Training hybrid 23-feature pipeline models...")
    X_hyb, y_hyb = generate_hybrid_synthetic_data(n_samples=6000)

    x_train, x_test, y_train, y_test = train_test_split(
        X_hyb, y_hyb, test_size=0.2, random_state=42, stratify=y_hyb
    )

    # Fit Scaler
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    # Fit SelectKBest
    selector = SelectKBest(score_func=f_classif, k=14)
    x_train_selected = selector.fit_transform(x_train_scaled, y_train)
    x_test_selected = selector.transform(x_test_scaled)

    # Train Random Forest
    rf = RandomForestClassifier(
        n_estimators=250,
        max_depth=14,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(x_train_selected, y_train)
    joblib.dump(rf, os.path.join(SAVE_DIR, "random_forest_model.joblib"))

    # Train Hybrid XGBoost
    xgb_hyb = XGBClassifier(
        n_estimators=300,
        max_depth=10,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
    )
    xgb_hyb.fit(x_train_selected, y_train)
    joblib.dump(xgb_hyb, os.path.join(SAVE_DIR, "xgboost_model.joblib"))

    # Train Hybrid Isolation Forest
    benign_train = x_train_selected[y_train == 0]
    if_hyb = IsolationForest(
        n_estimators=250,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )
    if_hyb.fit(benign_train)
    joblib.dump(if_hyb, os.path.join(SAVE_DIR, "isolation_forest.joblib"))

    # Save preprocessing objects
    joblib.dump(scaler, os.path.join(SAVE_DIR, "scaler.joblib"))
    joblib.dump(selector, os.path.join(SAVE_DIR, "feature_selector.joblib"))

    # Calculate validation metrics
    preds = xgb_hyb.predict(x_test_selected)
    accuracy = float((preds == y_test).mean())

    logger.info("Hybrid 23-feature models trained. Accuracy: %.2f%%", accuracy * 100)
    print(f"[SUCCESS] Seeding complete. All model artifacts generated and saved to {SAVE_DIR}/")
    print(f"   Legacy models: xgboost_model.pkl, isolation_forest.pkl")
    print(f"   Hybrid models: xgboost_model.joblib, isolation_forest.joblib, scaler.joblib, feature_selector.joblib")
    print(f"   Hybrid validation accuracy: {accuracy:.2%}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_models()
