import os
import zipfile
import logging
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE

from ml.feature_schema import FEATURE_NAMES

logger = logging.getLogger("kovirx.ml.train_on_datasets")
SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved_models")

LEGACY_FEATURE_NAMES = [
    "packet_rate", "beacon_interval", "dns_entropy", "flow_duration",
    "tcp_flags_encoded", "avg_packet_size", "failed_connections", "outbound_ratio",
]

def map_hybrid_features(df, dataset_name="cicids2017"):
    """Map CSE-CIC-IDS2017 columns to the 23-feature hybrid schema."""
    df.columns = [c.strip().lower() for c in df.columns]
    mapped = pd.DataFrame()

    mapped["event_count"] = 1.0
    mapped["network_event_count"] = 1.0
    mapped["dns_query_count"] = 0.0
    mapped["max_dns_entropy"] = 0.0
    mapped["avg_dns_entropy"] = 0.0

    # Flow Duration (microseconds to seconds)
    flow_dur = df.get("flow duration", 0.0)
    if dataset_name == "cicids2017":
        mapped["flow_duration"] = flow_dur / 1_000_000.0
    else:
        mapped["flow_duration"] = flow_dur

    mapped["packets_sent"] = df.get("total fwd packets", 0.0)
    mapped["packets_recv"] = df.get("total backward packets", 0.0)
    total_packets = mapped["packets_sent"] + mapped["packets_recv"]

    mapped["bytes_sent"] = df.get("fwd packets length total", df.get("totlen fwd pkts", 0.0))
    mapped["bytes_recv"] = df.get("bwd packets length total", df.get("totlen bwd pkts", 0.0))

    packet_rate = df.get("flow packets/s", 0.0)
    mask = (packet_rate == 0) | np.isinf(packet_rate) | np.isnan(packet_rate)
    packet_rate = np.where(mask & (mapped["flow_duration"] > 0), total_packets / mapped["flow_duration"], packet_rate)
    mapped["packet_rate"] = np.where(np.isinf(packet_rate) | np.isnan(packet_rate), 0.0, packet_rate)

    mapped["connection_count"] = 1.0
    mapped["unique_remote_ips"] = 1.0
    mapped["public_remote_ips"] = 1.0
    mapped["listening_ports"] = 0.0
    mapped["top_remote_port_count"] = 0.0
    mapped["failed_connection_ratio"] = 0.0

    # TCP Flag Score
    flag_cols = ["syn flag count", "rst flag count", "fin flag count", "psh flag count", "urg flag count"]
    flags_sum = sum(df.get(c, 0.0) for c in flag_cols)
    flag_score = np.where(total_packets > 0, flags_sum / total_packets, 0.0)
    mapped["tcp_flag_score"] = np.clip(flag_score, 0.0, 1.0)

    # Beacon Interval Score
    iat_mean = df.get("flow iat mean", 0.0)
    iat_std = df.get("flow iat std", 0.0)
    regularity = np.where(iat_mean > 0, 1.0 - (iat_std / iat_mean), 0.0)
    mapped["beacon_interval_score"] = np.clip(regularity, 0.0, 1.0)

    mapped["outbound_frequency"] = mapped["packet_rate"]
    mapped["cpu_percent"] = 0.0
    mapped["process_count"] = 0.0

    mapped = mapped.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return mapped[FEATURE_NAMES]

def map_legacy_features(df, dataset_name="cicids2017"):
    """Map CSE-CIC-IDS2017 columns to the 8-feature legacy schema."""
    df.columns = [c.strip().lower() for c in df.columns]
    mapped = pd.DataFrame()

    flow_dur = df.get("flow duration", 0.0)
    if dataset_name == "cicids2017":
        mapped["flow_duration"] = flow_dur / 1_000_000.0
    else:
        mapped["flow_duration"] = flow_dur

    pkts_sent = df.get("total fwd packets", 0.0)
    pkts_recv = df.get("total backward packets", 0.0)
    total_packets = pkts_sent + pkts_recv

    packet_rate = df.get("flow packets/s", 0.0)
    mask = (packet_rate == 0) | np.isinf(packet_rate) | np.isnan(packet_rate)
    packet_rate = np.where(mask & (mapped["flow_duration"] > 0), total_packets / mapped["flow_duration"], packet_rate)
    mapped["packet_rate"] = np.where(np.isinf(packet_rate) | np.isnan(packet_rate), 0.0, packet_rate)

    mapped["beacon_interval"] = df.get("flow iat std", 0.0)
    mapped["dns_entropy"] = 0.0

    # Encode TCP flags
    flag_cols = ["syn flag count", "rst flag count", "fin flag count", "psh flag count", "urg flag count"]
    flags_sum = sum(df.get(c, 0.0) for c in flag_cols)
    mapped["tcp_flags_encoded"] = flags_sum

    mapped["avg_packet_size"] = df.get("avg packet size", 0.0)
    mapped["failed_connections"] = 0.0

    outbound_ratio = np.where(total_packets > 0, pkts_sent / total_packets, 0.5)
    mapped["outbound_ratio"] = np.clip(outbound_ratio, 0.0, 1.0)

    mapped = mapped.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return mapped[LEGACY_FEATURE_NAMES]

def load_real_dataset():
    """Load and sample records from CSE-CIC-IDS2017 zip."""
    zip_path = "dataset1 (1).zip"
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Could not find dataset archive: {zip_path}")

    logger.info("Loading CSE-CIC-IDS2017 dataset from %s...", zip_path)
    with zipfile.ZipFile(zip_path) as z:
        # 1. Load Benign Monday
        logger.info("Loading Benign Monday...")
        df_benign = pd.read_parquet(z.open("Benign-Monday-no-metadata.parquet"))
        # Sample 30,000 benign records
        df_benign_sampled = df_benign.sample(n=min(30000, len(df_benign)), random_state=42)

        # 2. Load Botnet Friday
        logger.info("Loading Botnet Friday...")
        df_bot = pd.read_parquet(z.open("Botnet-Friday-no-metadata.parquet"))
        df_bot_only = df_bot[df_bot["Label"].astype(str).str.lower().str.strip() == "bot"]

        # 3. Load DoS Wednesday
        logger.info("Loading DoS Wednesday...")
        df_dos = pd.read_parquet(z.open("DoS-Wednesday-no-metadata.parquet"))
        df_dos_only = df_dos[df_dos["Label"].astype(str).str.lower().str.strip().str.startswith("dos")]
        df_dos_sampled = df_dos_only.sample(n=min(5000, len(df_dos_only)), random_state=42)

        # 4. Load DDoS Friday
        logger.info("Loading DDoS Friday...")
        df_ddos = pd.read_parquet(z.open("DDoS-Friday-no-metadata.parquet"))
        df_ddos_only = df_ddos[df_ddos["Label"].astype(str).str.lower().str.strip().str.startswith("ddos")]
        df_ddos_sampled = df_ddos_only.sample(n=min(5000, len(df_ddos_only)), random_state=42)

        # 5. Load Bruteforce Tuesday
        logger.info("Loading Bruteforce Tuesday...")
        df_bf = pd.read_parquet(z.open("Bruteforce-Tuesday-no-metadata.parquet"))
        df_bf_only = df_bf[df_bf["Label"].astype(str).str.lower().str.strip().str.contains("patator")]
        df_bf_sampled = df_bf_only.sample(n=min(5000, len(df_bf_only)), random_state=42)

    # Combine
    combined_df = pd.concat([
        df_benign_sampled,
        df_bot_only,
        df_dos_sampled,
        df_ddos_sampled,
        df_bf_sampled
    ], ignore_index=True)

    # Label encoding: 0 for Benign, 1 for anything else
    labels_str = combined_df["Label"].astype(str).str.lower().str.strip()
    y = np.where(labels_str.isin(["benign", "normal", "0"]), 0, 1)

    logger.info("Dataset loaded successfully. Total samples: %d (Benign: %d, Attacks: %d)",
                len(combined_df), np.sum(y == 0), np.sum(y == 1))

    return combined_df, y

def train_on_datasets():
    os.makedirs(SAVE_DIR, exist_ok=True)
    df, y = load_real_dataset()

    # ── 1. Train Legacy 8-Feature Models ───────────────────────────
    logger.info("Mapping and training legacy 8-feature models...")
    X_leg = map_legacy_features(df).to_numpy()

    # Legacy XGBoost
    xgb_leg = XGBClassifier(
        n_estimators=120,
        max_depth=6,
        learning_rate=0.1,
        eval_metric="logloss",
        random_state=42,
    )
    xgb_leg.fit(X_leg, y)
    joblib.dump(xgb_leg, os.path.join(SAVE_DIR, "xgboost_model.pkl"))

    # Legacy Isolation Forest
    if_leg = IsolationForest(
        n_estimators=100,
        contamination=0.15,
        random_state=42,
    )
    if_leg.fit(X_leg)
    joblib.dump(if_leg, os.path.join(SAVE_DIR, "isolation_forest.pkl"))

    # ── 2. Train Hybrid 23-Feature Models ──────────────────────────
    logger.info("Mapping and training hybrid 23-feature models...")
    X_hyb_df = map_hybrid_features(df)
    X_hyb = X_hyb_df.to_numpy()

    x_train, x_test, y_train, y_test = train_test_split(
        X_hyb, y, test_size=0.2, random_state=42, stratify=y
    )

    # Fit Preprocessing
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    selector = SelectKBest(score_func=f_classif, k=14)
    x_train_selected = selector.fit_transform(x_train_scaled, y_train)
    x_test_selected = selector.transform(x_test_scaled)

    # Oversample to handle class imbalance
    smote = SMOTE(random_state=42)
    x_train_balanced, y_train_balanced = smote.fit_resample(x_train_selected, y_train)

    # Train Random Forest
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(x_train_balanced, y_train_balanced)
    joblib.dump(rf, os.path.join(SAVE_DIR, "random_forest_model.joblib"))

    # Train Hybrid XGBoost
    xgb_hyb = XGBClassifier(
        n_estimators=250,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
    )
    xgb_hyb.fit(x_train_balanced, y_train_balanced)
    joblib.dump(xgb_hyb, os.path.join(SAVE_DIR, "xgboost_model.joblib"))

    # Train Hybrid Isolation Forest
    benign_train = x_train_selected[y_train == 0]
    if_hyb = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )
    if_hyb.fit(benign_train)
    joblib.dump(if_hyb, os.path.join(SAVE_DIR, "isolation_forest.joblib"))

    # Save preprocessing objects
    joblib.dump(scaler, os.path.join(SAVE_DIR, "scaler.joblib"))
    joblib.dump(selector, os.path.join(SAVE_DIR, "feature_selector.joblib"))

    # Metrics
    preds = xgb_hyb.predict(x_test_selected)
    accuracy = float((preds == y_test).mean())

    logger.info("Hybrid 23-feature models trained successfully. Accuracy: %.2f%%", accuracy * 100)
    print(f"\n[SUCCESS] Trained production ML models on CSE-CIC-IDS2017 dataset!")
    print(f"   Accuracy achieved: {accuracy:.2%}")
    print(f"   Saved output models to: {SAVE_DIR}/")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    train_on_datasets()
