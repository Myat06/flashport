"""
XGBoost risk scorer training script for FlashPort.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/train_risk_model.py

Reads:  data/training_declarations.csv
Writes: models/risk_model.xgb   (XGBoost model)
        models/model_info.json   (feature list, class mapping, metrics)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder

ROOT = Path(__file__).parent.parent
DATA_PATH  = ROOT / "data"  / "training_declarations.csv"
MODEL_DIR  = ROOT / "models"
MODEL_PATH = MODEL_DIR / "risk_model.xgb"
INFO_PATH  = MODEL_DIR / "model_info.json"


# ── Feature engineering ────────────────────────────────────────────────────────

DOC_TYPE_MAP  = {"commercial_invoice": 0, "bill_of_lading": 1, "packing_list": 2}
CONF_MAP      = {"high": 2, "medium": 1, "low": 0}
JALUR_MAP     = {"green": 0, "yellow": 1, "red": 2}
JALUR_REVERSE = {0: "green", 1: "yellow", 2: "red"}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    feat = pd.DataFrame()

    # Binary presence features
    feat["has_hs_code"]       = (df["hs_code"].fillna("").str.len() > 0).astype(int)
    feat["has_invoice_value"] = (df["invoice_value"].fillna("").str.len() > 0).astype(int)
    feat["has_container_id"]  = (df["container_id"].fillna("").str.len() > 0).astype(int)
    feat["has_importer"]      = (df["importer"].fillna("").str.len() > 0).astype(int)
    feat["has_exporter"]      = (df["exporter"].fillna("").str.len() > 0).astype(int)
    feat["has_vessel"]        = (df["vessel_name"].fillna("").str.len() > 0).astype(int)
    feat["has_port"]          = (df["port_of_origin"].fillna("").str.len() > 0).astype(int)

    # Numeric features
    feat["missing_field_count"] = df["missing_field_count"].fillna(0).astype(int)
    feat["confidence_score"]    = df["confidence_badge"].map(CONF_MAP).fillna(1).astype(int)
    feat["document_type_enc"]   = df["document_type"].map(DOC_TYPE_MAP).fillna(0).astype(int)
    feat["is_restricted_hs"]    = df["hs_restricted"].fillna(False).astype(int)

    # Invoice value (log-scaled to handle wide range)
    inv_val = pd.to_numeric(df["invoice_value_usd"], errors="coerce").fillna(0)
    feat["invoice_value_log"] = np.log1p(inv_val)
    feat["is_high_value"]     = (inv_val > 50_000).astype(int)
    feat["is_very_high_value"] = (inv_val > 200_000).astype(int)

    # High value without container — interaction feature
    feat["high_value_no_container"] = (
        (inv_val > 50_000) & (df["container_id"].fillna("").str.len() == 0)
    ).astype(int)

    # HS code prefix category (first 4 digits mapped to known risk categories)
    HIGH_SCRUTINY_PREFIXES = {"9301", "9302", "2710", "2711", "2902", "8471", "8517", "8542"}
    hs_prefix = df["hs_code"].fillna("").str.replace(".", "", regex=False).str[:4]
    feat["hs_high_scrutiny"] = hs_prefix.isin(HIGH_SCRUTINY_PREFIXES).astype(int)

    return feat


# ── Training ───────────────────────────────────────────────────────────────────

def train():
    print(f"Loading data from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"  {len(df)} records loaded")

    X = build_features(df)
    y = df["jalur_label"].astype(int)

    print(f"\nLabel distribution:")
    for jalur, label in JALUR_MAP.items():
        count = (y == label).sum()
        pct = count / len(y) * 100
        print(f"  {jalur:6} (label={label}): {count:4d} records ({pct:.1f}%)")

    print(f"\nFeatures ({len(X.columns)}): {list(X.columns)}")

    # ── Cross-validation ──────────────────────────────────────────────────────
    print("\nRunning 5-fold cross-validation...")
    model_cv = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model_cv, X, y, cv=cv, scoring="accuracy")
    print(f"  CV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # ── Final model on full dataset ───────────────────────────────────────────
    print("\nTraining final model on full dataset...")
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)

    # Train-set metrics (final model)
    y_pred = model.predict(X)
    print("\nTrain-set classification report:")
    print(classification_report(y, y_pred, target_names=["green", "yellow", "red"]))

    print("Confusion matrix (train set):")
    cm = confusion_matrix(y, y_pred)
    header = f"{'':10} {'pred_green':>12} {'pred_yellow':>12} {'pred_red':>10}"
    print(header)
    for i, row_name in enumerate(["true_green", "true_yellow", "true_red"]):
        print(f"  {row_name:10} {cm[i][0]:>12} {cm[i][1]:>12} {cm[i][2]:>10}")

    # ── Feature importance ────────────────────────────────────────────────────
    importance = dict(zip(X.columns, model.feature_importances_.tolist()))
    ranked = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print("\nTop feature importances:")
    for feat_name, score in ranked[:8]:
        bar = "█" * int(score * 40)
        print(f"  {feat_name:30} {score:.4f}  {bar}")

    # ── Save model ────────────────────────────────────────────────────────────
    MODEL_DIR.mkdir(exist_ok=True)
    model.save_model(str(MODEL_PATH))
    print(f"\nModel saved → {MODEL_PATH}")

    info = {
        "features": list(X.columns),
        "jalur_map": JALUR_REVERSE,
        "cv_accuracy_mean": float(cv_scores.mean()),
        "cv_accuracy_std": float(cv_scores.std()),
        "n_training_records": len(df),
        "label_distribution": {jalur: int((y == label).sum()) for jalur, label in JALUR_MAP.items()},
        "feature_importance": dict(ranked),
        "trained_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "note": "Trained on synthetic Cikarang Dry Port data. Retrain with real CEISA rejection data after August company visit.",
    }
    with open(INFO_PATH, "w") as f:
        json.dump(info, f, indent=2)
    print(f"Model info saved → {INFO_PATH}")

    return model, info


if __name__ == "__main__":
    train()
