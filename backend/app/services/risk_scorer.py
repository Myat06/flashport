"""Risk scorer — XGBoost model (trained on synthetic Cikarang Dry Port data).

Falls back to rule-based scoring if the model file is not found.
Retrain with real CEISA rejection data after August company visit:
    python scripts/train_risk_model.py
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from app.services.extractor import ExtractionResult

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_HIGH_RISK_HS_PREFIXES = {"8471", "8517", "8542", "9013", "2710", "2711", "9301", "9302"}
_HIGH_VALUE_THRESHOLD = 50_000

# Load XGBoost model once at startup
_MODEL      = None
_EXPLAINER  = None
_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "risk_model.xgb"

FEATURE_NAMES = [
    "has_hs_code", "has_invoice_value", "has_container_id", "has_importer",
    "has_exporter", "has_vessel", "has_port", "missing_field_count",
    "confidence_score", "document_type_enc", "is_restricted_hs",
    "invoice_value_log", "is_high_value", "is_very_high_value",
    "high_value_no_container", "hs_high_scrutiny",
]

FEATURE_LABELS = {
    "has_hs_code":            "HS Code present",
    "has_invoice_value":      "Invoice value present",
    "has_container_id":       "Container ID present",
    "has_importer":           "Importer identified",
    "has_exporter":           "Exporter identified",
    "has_vessel":             "Vessel name present",
    "has_port":               "Port of origin present",
    "missing_field_count":    "Missing critical fields",
    "confidence_score":       "OCR confidence level",
    "document_type_enc":      "Document type",
    "is_restricted_hs":       "Restricted HS code (weapons/chemicals)",
    "invoice_value_log":      "Invoice value (log scale)",
    "is_high_value":          "High value shipment (> USD 50k)",
    "is_very_high_value":     "Very high value (> USD 200k)",
    "high_value_no_container":"High value without container ID",
    "hs_high_scrutiny":       "HS code in scrutiny category",
}


def _load_model():
    global _MODEL, _EXPLAINER
    if _MODEL is not None:
        return _MODEL
    try:
        import xgboost as xgb
        import shap
        m = xgb.XGBClassifier()
        m.load_model(str(_MODEL_PATH))
        _MODEL    = m
        _EXPLAINER = shap.TreeExplainer(m)
        logger.info("XGBoost + SHAP explainer loaded from %s", _MODEL_PATH)
    except Exception as e:
        logger.warning("XGBoost model not loaded (%s) — using rule-based fallback", e)
        _MODEL = False
    return _MODEL


def compute_shap(features: list[float], predicted_class: int) -> list[dict]:
    """Return per-feature SHAP contributions for the predicted class."""
    if not _EXPLAINER:
        return []
    try:
        import numpy as np
        arr = np.array([features])
        # Use the Explanation API (shap >= 0.40) for consistent format
        explanation = _EXPLAINER(arr)
        vals = explanation.values  # shape: (n_samples, n_features, n_classes)
        if vals.ndim == 3:
            class_shap = vals[0, :, predicted_class]
        elif vals.ndim == 2:
            class_shap = vals[0, :]
        else:
            class_shap = vals
        return [
            {
                "feature":    FEATURE_NAMES[i],
                "label":      FEATURE_LABELS.get(FEATURE_NAMES[i], FEATURE_NAMES[i]),
                "value":      round(float(features[i]), 4),
                "shap_value": round(float(class_shap[i]), 4),
                "direction":  "increase" if class_shap[i] > 0 else "decrease",
            }
            for i in range(len(FEATURE_NAMES))
        ]
    except Exception as e:
        logger.warning("SHAP computation failed: %s", e)
        return []


def _build_features(result: ExtractionResult, confidence_badge: str,
                    watchlist_hits: list | None = None, db=None) -> list[float]:
    """Build the 16-feature vector matching train_risk_model.py build_features()."""
    import math

    hs = result.hs_code or ""
    inv_val_str = result.invoice_value or ""
    cont = result.container_id or ""
    imp = result.importer or ""
    exp = result.exporter or ""
    vessel = result.vessel_name or ""
    port = result.port_of_origin or ""

    # Parse invoice value
    try:
        num_str = "".join(c for c in inv_val_str if c.isdigit() or c == ".")
        inv_usd = float(num_str) if num_str else 0.0
    except ValueError:
        inv_usd = 0.0

    # Restricted HS check
    restricted_prefixes = {"9301", "9302", "2710", "2711", "2902"}
    high_scrutiny = {"8471", "8517", "8542", "9013", "2710", "2711", "9301", "9302"}
    hs_prefix = hs.replace(".", "")[:4]
    is_restricted = int(hs_prefix in restricted_prefixes)
    is_high_scrutiny = int(hs_prefix in high_scrutiny)

    critical = [hs, inv_val_str, cont, imp, exp, vessel, port]
    missing_count = sum(1 for f in critical if not f)

    conf_map = {"high": 2, "medium": 1, "low": 0}
    conf_score = conf_map.get(confidence_badge, 1)

    return [
        float(bool(hs)),           # has_hs_code
        float(bool(inv_val_str)),  # has_invoice_value
        float(bool(cont)),         # has_container_id
        float(bool(imp)),          # has_importer
        float(bool(exp)),          # has_exporter
        float(bool(vessel)),       # has_vessel
        float(bool(port)),         # has_port
        float(missing_count),      # missing_field_count
        float(conf_score),         # confidence_score
        0.0,                       # document_type_enc (unknown at score time)
        float(is_restricted),      # is_restricted_hs
        float(math.log1p(inv_usd)),# invoice_value_log
        float(inv_usd > 50_000),   # is_high_value
        float(inv_usd > 200_000),  # is_very_high_value
        float(inv_usd > 50_000 and not cont),  # high_value_no_container
        float(is_high_scrutiny),   # hs_high_scrutiny
    ]


def score(
    result: ExtractionResult,
    confidence_badge: str,
    db: "Session | None" = None,
    watchlist_hits: list[dict] | None = None,
) -> tuple[int, str, list[str], list[dict]]:
    """Return (risk_score 0-100, risk_badge, flagged_fields).

    Uses XGBoost model when available, falls back to rule-based scoring.
    DB rules and watchlist hits are always applied on top.
    """
    # ── Try XGBoost first ─────────────────────────────────────────────────────
    model = _load_model()
    if model:
        try:
            features = _build_features(result, confidence_badge, watchlist_hits, db)
            proba = model.predict_proba([features])[0]   # [p_green, p_yellow, p_red]
            predicted_label = int(np.argmax(proba))
            # Convert probability to 0-100 risk score
            # green=0→low risk, red=2→high risk
            risk_score = int(proba[1] * 40 + proba[2] * 100)
            risk_score = min(100, risk_score)

            # Flags from missing fields (use missing_critical if populated, else derive)
            flags: list[str] = []
            critical_check = {
                "hs_code": result.hs_code,
                "invoice_value": result.invoice_value,
                "container_id": result.container_id,
                "importer": result.importer,
            }
            missing_source = result.missing_critical if result.missing_critical else [
                f for f, v in critical_check.items() if not v
            ]
            for field in missing_source:
                flags.append(f"missing:{field}")
            if confidence_badge == "low":
                flags.append("low_ocr_confidence")
            elif confidence_badge == "medium":
                flags.append("medium_ocr_confidence")

            # Watchlist always overrides
            # Add structural flags based on features
            if features[15] == 1.0:  # hs_high_scrutiny
                flags.append("hs_high_scrutiny_category")
            if features[10] == 1.0:  # is_restricted_hs
                flags.append("hs_restricted_category")

            for hit in (watchlist_hits or []):
                risk_score = min(100, risk_score + 25)
                flags.append(f"watchlist:{hit['entity_type']}:{hit['value']}")

            # DB rules on top
            if db is not None:
                risk_score_adj, flags = _apply_db_rules(db, result, risk_score, flags)
                risk_score = min(100, risk_score_adj)

            badge = "green" if risk_score < 30 else "yellow" if risk_score < 70 else "red"
            badge_label_idx = {"green": 0, "yellow": 1, "red": 2}[badge]
            shap_values = compute_shap(features, badge_label_idx)
            return risk_score, badge, list(dict.fromkeys(flags)), shap_values
        except Exception as e:
            logger.warning("XGBoost prediction failed (%s) — using rule-based fallback", e)

    # ── Rule-based fallback ───────────────────────────────────────────────────
    points = 0
    flags: list[str] = []

    # Missing critical fields
    for missing in result.missing_critical:
        points += 20
        flags.append(f"missing:{missing}")

    # OCR confidence
    if confidence_badge == "low":
        points += 15
        flags.append("low_ocr_confidence")
    elif confidence_badge == "medium":
        points += 5

    # HS code baseline
    if result.hs_code:
        prefix = result.hs_code.replace(".", "")[:4]
        if prefix in _HIGH_RISK_HS_PREFIXES:
            points += 10
            flags.append("hs_high_scrutiny_category")
    else:
        points += 10
        flags.append("missing:hs_code")

    # High value without container
    if result.invoice_value and result.container_id is None:
        try:
            value_str = result.invoice_value.split()[-1].replace(",", "")
            if float(value_str) > _HIGH_VALUE_THRESHOLD:
                points += 15
                flags.append("high_value_no_container_id")
        except (ValueError, IndexError):
            pass

    if not result.importer:
        points += 10
        flags.append("missing:importer")

    # Watchlist hits
    for hit in (watchlist_hits or []):
        points += 25
        flags.append(f"watchlist:{hit['entity_type']}:{hit['value']}")

    # Manager-configured DB rules
    if db is not None:
        points, flags = _apply_db_rules(db, result, points, flags)

    risk_score = min(points, 100)
    badge = "green" if risk_score < 30 else "yellow" if risk_score < 70 else "red"
    return risk_score, badge, list(dict.fromkeys(flags)), []  # no SHAP in fallback


def _apply_db_rules(db, result: ExtractionResult, points: int, flags: list[str]):
    from app.models.risk_rule import RiskRule

    rules = db.query(RiskRule).filter(RiskRule.is_active == True).all()  # noqa: E712
    field_map = {
        "hs_code": result.hs_code or "",
        "importer": result.importer or "",
        "exporter": result.exporter or "",
        "invoice_value": result.invoice_value or "",
        "container_id": result.container_id or "",
        "net_weight": result.net_weight or "",
        "vessel_name": result.vessel_name or "",
        "port_of_origin": result.port_of_origin or "",
    }

    for rule in rules:
        field_val = field_map.get(rule.field, "")
        matched = False

        if rule.condition == "missing":
            matched = not field_val
        elif rule.condition == "starts_with":
            matched = field_val.upper().startswith(rule.value.upper())
        elif rule.condition == "equals":
            matched = field_val.strip().upper() == rule.value.strip().upper()
        elif rule.condition == "contains":
            matched = rule.value.upper() in field_val.upper()
        elif rule.condition == "gt":
            try:
                matched = float(field_val.replace(",", "").split()[-1]) > float(rule.value)
            except (ValueError, IndexError):
                pass

        if matched:
            points += rule.risk_boost
            flags.append(rule.flag_label or rule.name)

    return points, flags
