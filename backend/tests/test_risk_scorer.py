from app.services.extractor import ExtractionResult
from app.services.risk_scorer import score


def test_clean_declaration_is_green():
    result = ExtractionResult(
        hs_code="6104.43.00",
        invoice_value="USD 3,000.00",
        container_id="MSCU9876543",
        importer="PT Bersama Maju",
    )
    risk_score, badge, flags = score(result, "high")
    assert badge == "green"
    assert risk_score < 30


def test_missing_all_fields_is_red():
    from app.services.extractor import extract_fields
    result = extract_fields("")
    risk_score, badge, flags = score(result, "low")
    assert badge == "red"
    assert risk_score >= 70


def test_low_confidence_adds_risk():
    r_high = ExtractionResult(hs_code="6104.43.00", invoice_value="USD 100.00",
                               container_id="ABCD1234567", importer="PT A")
    r_low = ExtractionResult(hs_code="6104.43.00", invoice_value="USD 100.00",
                              container_id="ABCD1234567", importer="PT A")
    score_high, _, _ = score(r_high, "high")
    score_low, _, _ = score(r_low, "low")
    assert score_low > score_high


def test_high_risk_hs_code_flagged():
    result = ExtractionResult(
        hs_code="8471.30.00",
        invoice_value="USD 500.00",
        container_id="ABCD1234567",
        importer="PT B",
    )
    risk_score, _, flags = score(result, "high")
    assert "hs_high_scrutiny_category" in flags
