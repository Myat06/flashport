"""
XGBoost risk scorer training script — FlashPort.

Reads:  data/training_declarations.csv
Writes: models/risk_model.xgb
        models/model_info.json

Usage:
    cd backend
    source venv/bin/activate
    python scripts/train_risk_model.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score

ROOT       = Path(__file__).parent.parent
DATA_PATH  = ROOT / "data"  / "training_declarations.csv"
MODEL_DIR  = ROOT / "models"
MODEL_PATH = MODEL_DIR / "risk_model.xgb"
INFO_PATH  = MODEL_DIR / "model_info.json"

DOC_TYPE_ENC  = {"commercial_invoice": 0, "bill_of_lading": 1, "packing_list": 2}
CONF_ENC      = {"high": 2, "medium": 1, "low": 0}
JALUR_REVERSE = {0: "green", 1: "yellow", 2: "red"}

HIGH_SCRUTINY_HS = {"9301", "9302", "2710", "2711", "2902", "8471", "8517", "8542", "9013"}
RESTRICTED_HS    = {"9301", "9302", "2710", "2711", "2902"}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    feat = pd.DataFrame()

    # ── Binary presence features ───────────────────────────────────────────────
    feat["has_hs_code"]       = (df["hs_code"].fillna("").str.len() > 0).astype(int)
    feat["has_invoice_value"] = (df["invoice_value"].fillna("").str.len() > 0).astype(int)
    feat["has_container_id"]  = (df["container_id"].fillna("").str.len() > 0).astype(int)
    feat["has_importer"]      = (df["importer"].fillna("").str.len() > 0).astype(int)
    feat["has_exporter"]      = (df["exporter"].fillna("").str.len() > 0).astype(int)
    feat["has_vessel"]        = (df["vessel_name"].fillna("").str.len() > 0).astype(int)
    feat["has_port"]          = (df["port_of_origin"].fillna("").str.len() > 0).astype(int)

    # ── Doc-type-aware missing field count ────────────────────────────────────
    # Count only fields that are EXPECTED for this doc type — aligns with
    # the runtime risk scorer which filters field_defs by document_type.
    def doc_aware_missing(row):
        dt    = row.get("document_type", "commercial_invoice")
        count = 0
        # Always expected
        for f in ("importer", "exporter", "container_id"):
            if not row.get(f):
                count += 1
        # Doc-type-specific
        if dt == "commercial_invoice":
            for f in ("hs_code", "invoice_value", "invoice_number"):
                if not row.get(f):
                    count += 1
        elif dt == "bill_of_lading":
            for f in ("vessel_name", "port_of_origin"):
                if not row.get(f):
                    count += 1
        elif dt == "packing_list":
            for f in ("net_weight", "gross_weight", "carton_count"):
                if not row.get(f):
                    count += 1
        return count

    feat["missing_field_count"] = df.apply(doc_aware_missing, axis=1)

    # ── Other scalar features ──────────────────────────────────────────────────
    feat["confidence_score"]  = df["confidence_badge"].map(CONF_ENC).fillna(1).astype(int)
    feat["document_type_enc"] = df["document_type"].map(DOC_TYPE_ENC).fillna(0).astype(int)

    hs_prefix = df["hs_code"].fillna("").str.replace(".", "", regex=False).str[:4]
    feat["is_restricted_hs"] = hs_prefix.isin(RESTRICTED_HS).astype(int)

    # ── Invoice value features ─────────────────────────────────────────────────
    inv_val = pd.to_numeric(df["invoice_value_usd"], errors="coerce").fillna(0)
    feat["invoice_value_log"]     = np.log1p(inv_val)
    feat["is_high_value"]         = (inv_val > 50_000).astype(int)
    feat["is_very_high_value"]    = (inv_val > 200_000).astype(int)

    # Only penalise high-value + no-container for commercial invoices
    feat["high_value_no_container"] = (
        (inv_val > 50_000)
        & (df["container_id"].fillna("").str.len() == 0)
        & (df["document_type"] == "commercial_invoice")
    ).astype(int)

    feat["hs_high_scrutiny"] = hs_prefix.isin(HIGH_SCRUTINY_HS).astype(int)

    return feat


def train():
    print(f"Loading data from {DATA_PATH}")
    if not DATA_PATH.exists():
        print(f"ERROR: {DATA_PATH} not found.")
        print("Run:  python scripts/generate_training_data.py")
        sys.exit(1)

    df = pd.read_csv(DATA_PATH)
    print(f"  {len(df):,} records loaded")

    X = build_features(df)
    y = df["jalur_label"].astype(int)

    print(f"\nLabel distribution:")
    for jalur, label in [("green", 0), ("yellow", 1), ("red", 2)]:
        n   = int((y == label).sum())
        pct = n / len(y) * 100
        bar = "█" * int(pct / 2)
        print(f"  {jalur:6}  {n:5d}  ({pct:4.1f}%)  {bar}")

    print(f"\nFeatures ({len(X.columns)}): {list(X.columns)}")

    # ── Class weights (penalise red misses more heavily) ─────────────────────
    # Red = 3× weight, yellow = 2×, green = 1× — false negatives on red are dangerous
    sample_weights = y.map({0: 1.0, 1: 2.0, 2: 3.0}).values

    # ── 5-fold cross-validation ───────────────────────────────────────────────
    print("\nRunning 5-fold stratified cross-validation…")
    params = dict(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.04,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    cv       = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_model = xgb.XGBClassifier(**params)
    cv_scores = cross_val_score(cv_model, X, y, cv=cv, scoring="accuracy",
                                fit_params={"sample_weight": sample_weights})
    print(f"  CV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # ── Final model on full dataset ───────────────────────────────────────────
    print("\nTraining final model on full dataset…")
    model = xgb.XGBClassifier(**params)
    model.fit(X, y, sample_weight=sample_weights)

    y_pred = model.predict(X)
    print("\nClassification report (training set):")
    print(classification_report(y, y_pred, target_names=["green", "yellow", "red"]))

    print("Confusion matrix:")
    cm = confusion_matrix(y, y_pred)
    labels = ["green", "yellow", "red"]
    col_w = 10
    print(f"{'':12}" + "".join(f"pred_{l:6}" for l in labels))
    for i, true_l in enumerate(labels):
        row = f"  true_{true_l:6}" + "".join(f"{cm[i][j]:>{col_w}}" for j in range(3))
        print(row)

    # ── Feature importances ───────────────────────────────────────────────────
    importance = dict(zip(X.columns, model.feature_importances_.tolist()))
    ranked     = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print("\nFeature importances:")
    for name, score in ranked:
        bar = "█" * int(score * 50)
        print(f"  {name:30}  {score:.4f}  {bar}")

    # ── Save ──────────────────────────────────────────────────────────────────
    MODEL_DIR.mkdir(exist_ok=True)
    model.save_model(str(MODEL_PATH))
    print(f"\nModel saved → {MODEL_PATH}")

    info = {
        "features":              list(X.columns),
        "jalur_map":             JALUR_REVERSE,
        "cv_accuracy_mean":      float(cv_scores.mean()),
        "cv_accuracy_std":       float(cv_scores.std()),
        "n_training_records":    len(df),
        "label_distribution":    {j: int((y == l).sum()) for j, l in [("green",0),("yellow",1),("red",2)]},
        "feature_importance":    dict(ranked),
        "trained_at":            __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "doc_type_aware":        True,
        "class_weighted":        True,
        "red_fp_weight":         3.0,
    }
    with open(INFO_PATH, "w") as f:
        json.dump(info, f, indent=2)
    print(f"Info saved   → {INFO_PATH}")
    return model, info


if __name__ == "__main__":
    train()
