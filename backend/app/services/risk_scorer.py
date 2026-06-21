"""Rule-based risk scorer for Phase 1 demo.

Replaced by trained XGBoost model in August after company visit data is collected.
Score range: 0 (clean) to 100 (high anomaly).
"""
from app.services.extractor import ExtractionResult

# HS codes that trigger elevated scrutiny (electronics with hazard tax codes)
_HIGH_RISK_HS_PREFIXES = {"8471", "8517", "8542", "9013", "2710", "2711", "9301", "9302"}

# Known suspicious value thresholds (USD) that trigger CIF checks
_HIGH_VALUE_THRESHOLD = 50_000


def score(result: ExtractionResult, confidence_badge: str) -> tuple[int, str, list[str]]:
    """Return (risk_score 0-100, risk_badge, flagged_fields)."""
    score = 0
    flags: list[str] = []

    # Missing critical fields adds significant risk
    for missing in result.missing_critical:
        score += 20
        flags.append(f"missing:{missing}")

    # Low confidence OCR is itself a risk signal
    if confidence_badge == "low":
        score += 15
        flags.append("low_ocr_confidence")
    elif confidence_badge == "medium":
        score += 5

    # HS code present but in high-scrutiny category
    if result.hs_code:
        prefix = result.hs_code.replace(".", "")[:4]
        if prefix in _HIGH_RISK_HS_PREFIXES:
            score += 10
            flags.append("hs_high_scrutiny_category")
    else:
        score += 10
        flags.append("missing:hs_code")

    # High declared value without matching container ID
    if result.invoice_value and result.container_id is None:
        try:
            value_str = result.invoice_value.split()[-1].replace(",", "")
            if float(value_str) > _HIGH_VALUE_THRESHOLD:
                score += 15
                flags.append("high_value_no_container_id")
        except (ValueError, IndexError):
            pass

    # No importer/consignee identified
    if not result.importer:
        score += 10
        flags.append("missing:importer")

    risk_score = min(score, 100)

    if risk_score < 30:
        badge = "green"
    elif risk_score < 70:
        badge = "yellow"
    else:
        badge = "red"

    return risk_score, badge, flags
