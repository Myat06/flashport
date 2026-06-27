"""Field validation service — data-driven.

Reads active field definitions from the DB for priority and iterates over them.
Admin can add new fields via the /field-definitions API; no code change needed.

Built-in format checks still run for the 11 known field keys.
Manager-configured DB rules (field_validation_rules table) run on top.
"""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.services.extractor import ExtractionResult

logger = logging.getLogger(__name__)

# Risk boost per priority tier when a field is present but fails format/range validation
PRIORITY_RISK_BOOST: dict[str, int] = {
    "critical": 15,
    "important": 8,
    "optional": 3,
}

_CURRENCY_RE = re.compile(r"(USD|EUR|SGD|CNY|IDR|JPY)\s*[\d,]+", re.IGNORECASE)
_HS_RE       = re.compile(r"^\d{4}\.?\d{2}\.?\d{2,4}$")
_CONT_RE     = re.compile(r"^[A-Z]{4}\d{7}$")


def validate_fields(
    extraction: "ExtractionResult",
    field_defs: list[dict],
    db: "Session | None" = None,
    bboxes: dict[str, dict] | None = None,
) -> list[dict]:
    """Return one validation result dict per active field definition.

    Each dict: {field_name, value, is_valid, priority, message, bbox}

    Args:
        extraction:  Dynamic ExtractionResult from extract_fields().
        field_defs:  Active field definitions (list of dicts with field_key, priority, …).
        db:          DB session for manager-configured validation rules.
        bboxes:      Pixel bounding boxes keyed by field_key.
    """
    bboxes  = bboxes or {}
    results = []

    for fd in field_defs:
        field_key = fd["field_key"]
        priority  = fd.get("priority", "optional")
        value     = extraction.get(field_key)
        bbox      = bboxes.get(field_key)

        is_valid, message = _check_builtin(field_key, value, fd.get("display_label", field_key))

        # Manager-configured DB rules (run only if built-in check passed)
        if is_valid and db is not None:
            err = _check_db_rules(field_key, value, db)
            if err:
                is_valid, message = False, err

        results.append({
            "field_name": field_key,
            "value":      value,
            "is_valid":   is_valid,
            "priority":   priority,
            "message":    message,
            "bbox":       bbox,
        })

    return results


def validation_risk_boost(results: list[dict]) -> int:
    """Extra risk points from format/range violations (field present but wrong)."""
    total = 0
    for r in results:
        if not r["is_valid"] and r["value"] is not None:
            total += PRIORITY_RISK_BOOST.get(r["priority"], 0)
    return total


# ── Built-in format checks for known field keys ───────────────────────────────

def _check_builtin(field_key: str, value: str | None, label: str) -> tuple[bool, str | None]:
    """Return (is_valid, error_message | None)."""
    if value is None:
        return False, f"{label} is missing"

    v = value.strip()

    if field_key == "hs_code":
        if not _HS_RE.match(v):
            return False, "HS code must be 8-digit format (e.g. 8471.30.10)"

    elif field_key == "container_id":
        if not _CONT_RE.fullmatch(v):
            return False, "Container ID must be 4 uppercase letters + 7 digits (ISO 6346)"

    elif field_key == "invoice_value":
        if not _CURRENCY_RE.search(v):
            return False, "Invoice value must include a currency code (e.g. USD 75,000)"

    elif field_key in ("net_weight", "gross_weight"):
        num_str = re.sub(r"[^\d.]", "", v.split()[0] if v.split() else "")
        try:
            num = float(num_str) if num_str else 0.0
            if num <= 0:
                return False, f"{label} must be greater than 0"
            if num > 500_000:
                return False, f"{label} exceeds maximum (500,000 kg)"
        except ValueError:
            return False, f"{label} must be a numeric value"

    elif field_key == "carton_count":
        num_str = re.sub(r"[^\d]", "", v)
        try:
            num = int(num_str) if num_str else 0
            if num <= 0:
                return False, "Carton count must be greater than 0"
            if num > 99_999:
                return False, "Carton count exceeds maximum (99,999)"
        except ValueError:
            return False, "Carton count must be a whole number"

    # For custom admin-defined fields with no built-in check: pass as valid if present
    return True, None


# ── Manager-configured DB rules ───────────────────────────────────────────────

def _check_db_rules(field_key: str, value: str | None, db) -> str | None:
    """Return an error message if any active DB rule fires, else None."""
    try:
        from app.models.field_validation_rule import FieldValidationRule
        rules = (
            db.query(FieldValidationRule)
            .filter(
                FieldValidationRule.field_name == field_key,
                FieldValidationRule.is_active == True,  # noqa: E712
            )
            .all()
        )
    except Exception as e:
        logger.warning("Could not load DB validation rules: %s", e)
        return None

    val = value or ""
    for rule in rules:
        fired = False

        if rule.rule_type == "required":
            fired = not val

        elif rule.rule_type == "regex" and rule.pattern:
            try:
                fired = not re.search(rule.pattern, val)
            except re.error:
                pass

        elif rule.rule_type == "range":
            num_str = re.sub(r"[^\d.]", "", val.split()[0] if val.split() else "")
            try:
                num = float(num_str) if num_str else None
                if num is not None:
                    if rule.min_val and num < float(rule.min_val):
                        fired = True
                    if rule.max_val and num > float(rule.max_val):
                        fired = True
            except (ValueError, TypeError):
                pass

        elif rule.rule_type == "enum" and rule.allowed_values:
            allowed = [v.strip().upper() for v in rule.allowed_values.split(",")]
            fired = val.upper() not in allowed

        elif rule.rule_type == "max_length" and rule.max_length:
            fired = len(val) > rule.max_length

        if fired:
            return rule.error_message or f"{field_key} failed validation rule: {rule.name}"

    return None
