import argparse
import json
from pathlib import Path
import joblib
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from ml.feature_schema import FEATURE_NAMES

FEATURE_COLUMNS = FEATURE_NAMES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the KOVIRX hybrid XGBoost and Isolation Forest pipeline."
    )
    parser.add_argument("--input", required=True, help="Path to a cleaned feature CSV.")
    parser.add_argument(
        "--label-column",
        default="label",
        help="Binary label column. Use 1 for botnet/attack and 0 for benign.",
    )
    parser.add_argument(
        "--output-dir",
        default="ml/saved_models",
        help="Directory where model artifacts will be written.",
    )
    parser.add_argument(
        "--k-best",
        type=int,
        default=14,
        help="Number of selected features to keep after preprocessing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = pd.read_csv(input_path)
    missing_columns = [column for column in FEATURE_COLUMNS + [args.label_column] if column not in dataset]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    dataset = dataset[FEATURE_COLUMNS + [args.label_column]].copy()
    dataset = dataset.replace([float("inf"), float("-inf")], pd.NA)
    dataset = dataset.fillna(0)

    features = dataset[FEATURE_COLUMNS]
    labels = dataset[args.label_column].astype(int)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    selector = SelectKBest(score_func=f_classif, k=min(args.k_best, len(FEATURE_COLUMNS)))
    x_train_selected = selector.fit_transform(x_train_scaled, y_train)
    x_test_selected = selector.transform(x_test_scaled)

    smote = SMOTE(random_state=42)
    x_train_balanced, y_train_balanced = smote.fit_resample(x_train_selected, y_train)

    fast_model = RandomForestClassifier(
        n_estimators=250,
        max_depth=14,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    fast_model.fit(x_train_balanced, y_train_balanced)

    xgboost_model = XGBClassifier(
        n_estimators=300,
        max_depth=10,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
    )
    xgboost_model.fit(x_train_balanced, y_train_balanced)

    benign_train = x_train_selected[y_train.to_numpy() == 0]
    isolation_model = IsolationForest(
        n_estimators=250,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )
    isolation_model.fit(benign_train)

    probabilities = xgboost_model.predict_proba(x_test_selected)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    metrics = {
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "classification_report": classification_report(y_test, predictions, output_dict=True),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        "selected_features": [
            FEATURE_COLUMNS[index]
            for index in selector.get_support(indices=True)
        ],
    }

    joblib.dump(fast_model, output_dir / "random_forest_model.joblib")
    joblib.dump(xgboost_model, output_dir / "xgboost_model.joblib")
    joblib.dump(isolation_model, output_dir / "isolation_forest.joblib")
    joblib.dump(scaler, output_dir / "scaler.joblib")
    joblib.dump(selector, output_dir / "feature_selector.joblib")
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Artifacts written to: {output_dir}")
    print(f"ROC AUC: {metrics['roc_auc']:.4f}")
    print("Selected features:")
    for feature in metrics["selected_features"]:
        print(f"- {feature}")


if __name__ == "__main__":
    main()
