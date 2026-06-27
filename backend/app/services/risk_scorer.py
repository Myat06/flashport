"""Risk scorer — XGBoost model (fixed feature vector) + dynamic field-weight fallback.

XGBoost: still runs with its trained 16-feature vector for the 11 built-in fields.
Dynamic risk: admin-configured risk_weight per field_definition is applied on top
              for ANY field (both built-in and custom admin-defined).
              In the rule-based fallback, risk_weight fully replaces hardcoded penalties.

Retrain XGBoost with real CEISA rejection data after August company visit:
    python scripts/train_risk_model.py
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from app.services.extractor import ExtractionResult

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_HIGH_RISK_HS_PREFIXES = {"8471", "8517", "8542", "9013", "2710", "2711", "9301", "9302"}

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
    "has_hs_code":             "HS Code present",
    "has_invoice_value":       "Invoice value present",
    "has_container_id":        "Container ID present",
    "has_importer":            "Importer identified",
    "has_exporter":            "Exporter identified",
    "has_vessel":              "Vessel name present",
    "has_port":                "Port of origin present",
    "missing_field_count":     "Missing critical fields",
    "confidence_score":        "OCR confidence level",
    "document_type_enc":       "Document type",
    "is_restricted_hs":        "Restricted HS code (weapons/chemicals)",
    "invoice_value_log":       "Invoice value (log scale)",
    "is_high_value":           "High value shipment (> USD 50k)",
    "is_very_high_value":      "Very high value (> USD 200k)",
    "high_value_no_container": "High value without container ID",
    "hs_high_scrutiny":        "HS code in scrutiny category",
}

_DOC_TYPE_ENC = {"commercial_invoice": 0.0, "bill_of_lading": 1.0, "packing_list": 2.0}

# Fields that are already accounted for in the XGBoost feature vector.
# We do NOT add their risk_weight again on top of XGBoost to avoid double-counting.
_XGB_MANAGED_FIELDS = {
    "hs_code", "invoice_value", "container_id", "importer",
    "exporter", "vessel_name", "port_of_origin",
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
        _MODEL     = m
        _EXPLAINER = shap.TreeExplainer(m)
        logger.info("XGBoost + SHAP loaded from %s", _MODEL_PATH)
    except Exception as e:
        logger.warning("XGBoost not loaded (%s) — rule-based fallback", e)
        _MODEL = False
    return _MODEL


def compute_shap(features: list[float], predicted_class: int) -> list[dict]:
    if not _EXPLAINER:
        return []
    try:
        arr         = np.array([features])
        explanation = _EXPLAINER(arr)
        vals        = explanation.values
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
        logger.warning("SHAP failed: %s", e)
        return []


def _build_xgb_features(
    result: ExtractionResult,
    confidence_badge: str,
    document_type: str = "",
) -> list[float]:
    """Build the fixed 16-feature vector for the trained XGBoost model."""
    hs          = result.get("hs_code") or ""
    inv_val_str = result.get("invoice_value") or ""
    cont        = result.get("container_id") or ""
    imp         = result.get("importer") or ""
    exp         = result.get("exporter") or ""
    vessel      = result.get("vessel_name") or ""
    port        = result.get("port_of_origin") or ""

    try:
        num_str = "".join(c for c in inv_val_str if c.isdigit() or c == ".")
        inv_usd = float(num_str) if num_str else 0.0
    except ValueError:
        inv_usd = 0.0

    restricted_prefixes = {"9301", "9302", "2710", "2711", "2902"}
    high_scrutiny       = {"8471", "8517", "8542", "9013", "2710", "2711", "9301", "9302"}
    hs_prefix           = hs.replace(".", "")[:4]

    critical    = [hs, inv_val_str, cont, imp, exp, vessel, port]
    missing_cnt = sum(1 for f in critical if not f)
    conf_score  = {"high": 2, "medium": 1, "low": 0}.get(confidence_badge, 1)

    return [
        float(bool(hs)),
        float(bool(inv_val_str)),
        float(bool(cont)),
        float(bool(imp)),
        float(bool(exp)),
        float(bool(vessel)),
        float(bool(port)),
        float(missing_cnt),
        float(conf_score),
        _DOC_TYPE_ENC.get(document_type, 0.0),
        float(hs_prefix in restricted_prefixes),
        float(math.log1p(inv_usd)),
        float(inv_usd > 50_000),
        float(inv_usd > 200_000),
        float(inv_usd > 50_000 and not cont),
        float(hs_prefix in high_scrutiny),
    ]


def score(
    result: ExtractionResult,
    confidence_badge: str,
    field_defs: list[dict],
    db: "Session | None" = None,
    watchlist_hits: list[dict] | None = None,
    document_type: str = "",
) -> tuple[int, str, list[str], list[dict]]:
    """Compute risk score (0-100), badge, flagged fields, and SHAP values.

    Args:
        result:          Dynamic extraction result.
        confidence_badge: 'high' | 'medium' | 'low'
        field_defs:      Active field definitions (risk_weight per field).
        db:              DB session for manager-configured risk rules.
        watchlist_hits:  List of watchlist matches.
        document_type:   Document type value string.
    """
    # ── Try XGBoost first ─────────────────────────────────────────────────────
    model = _load_model()
    if model:
        try:
            features      = _build_xgb_features(result, confidence_badge, document_type)
            proba         = model.predict_proba([features])[0]
            risk_score    = int(proba[1] * 40 + proba[2] * 100)
            risk_score    = min(100, risk_score)
            badge_idx     = int(np.argmax(proba))

            flags: list[str] = []

            # Flags from missing critical fields
            for fk in result.missing_critical:
                flags.append(f"missing:{fk}")

            if confidence_badge == "low":
                flags.append("low_ocr_confidence")
            elif confidence_badge == "medium":
                flags.append("medium_ocr_confidence")

            if features[15] == 1.0:
                flags.append("hs_high_scrutiny_category")
            if features[10] == 1.0:
                flags.append("hs_restricted_category")

            # Watchlist always adds on top
            for hit in (watchlist_hits or []):
                risk_score = min(100, risk_score + 25)
                flags.append(f"watchlist:{hit['entity_type']}:{hit['value']}")

            # Dynamic risk for custom fields NOT already in XGBoost features
            for fd in field_defs:
                key    = fd["field_key"]
                weight = fd.get("risk_weight", 0)
                if key in _XGB_MANAGED_FIELDS or not weight:
                    continue
                if not result.get(key):
                    risk_score = min(100, risk_score + weight)
                    if f"missing:{key}" not in flags:
                        flags.append(f"missing:{key}")

            # Manager-configured DB rules
            if db is not None:
                risk_score, flags = _apply_db_rules(db, result, risk_score, flags)
                risk_score = min(100, risk_score)

            badge      = "green" if risk_score < 30 else "yellow" if risk_score < 70 else "red"
            badge_lbl  = {"green": 0, "yellow": 1, "red": 2}[badge]
            shap_vals  = compute_shap(features, badge_lbl)
            return risk_score, badge, list(dict.fromkeys(flags)), shap_vals

        except Exception as e:
            logger.warning("XGBoost prediction failed (%s) — rule-based fallback", e)

    # ── Rule-based fallback — fully dynamic from field_defs ──────────────────
    points: int     = 0
    flags: list[str] = []

    # OCR confidence penalty
    if confidence_badge == "low":
        points += 15
        flags.append("low_ocr_confidence")
    elif confidence_badge == "medium":
        points += 5

    # Dynamic missing-field penalties from field_definitions.risk_weight
    for fd in field_defs:
        key    = fd["field_key"]
        weight = fd.get("risk_weight", 0)
        if not result.get(key) and weight > 0:
            points += weight
            flags.append(f"missing:{key}")

    # HS code high-scrutiny bonus (independent of risk_weight)
    hs = result.get("hs_code") or ""
    if hs:
        prefix = hs.replace(".", "")[:4]
        if prefix in _HIGH_RISK_HS_PREFIXES:
            points += 10
            flags.append("hs_high_scrutiny_category")

    # High-value shipment without container
    inv_val_str = result.get("invoice_value") or ""
    container   = result.get("container_id")
    if inv_val_str and not container:
        try:
            num_str = "".join(c for c in inv_val_str if c.isdigit() or c == ".")
            if float(num_str) > 50_000:
                points += 15
                flags.append("high_value_no_container_id")
        except ValueError:
            pass

    # Watchlist hits
    for hit in (watchlist_hits or []):
        points += 25
        flags.append(f"watchlist:{hit['entity_type']}:{hit['value']}")

    # Manager-configured DB rules
    if db is not None:
        points, flags = _apply_db_rules(db, result, points, flags)

    risk_score = min(points, 100)
    badge      = "green" if risk_score < 30 else "yellow" if risk_score < 70 else "red"
    return risk_score, badge, list(dict.fromkeys(flags)), []


def _apply_db_rules(
    db,
    result: ExtractionResult,
    points: int,
    flags: list[str],
) -> tuple[int, list[str]]:
    """Apply manager-configured risk rules from the DB. Fully dynamic field lookup."""
    try:
        from app.models.risk_rule import RiskRule
        rules = db.query(RiskRule).filter(RiskRule.is_active == True).all()  # noqa: E712
    except Exception as e:
        logger.warning("Could not load risk rules: %s", e)
        return points, flags

    # Build field map from all extracted fields (dynamic)
    field_map = {key: (result.get(key) or "") for key in result.keys()}

    for rule in rules:
        field_val = field_map.get(rule.field, "")
        matched   = False

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
