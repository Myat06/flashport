from app.services.extractor import ExtractionResult
from app.services.risk_scorer import score


def test_clean_declaration_is_green():
    result = ExtractionResult(
        hs_code="6104.43.00",
        invoice_value="USD 3,000.00",
        container_id="MSCU9876543",
        importer="PT Bersama Maju",
    )
    risk_score, badge, flags, shap = score(result, "high")
    assert badge == "green"
    assert risk_score < 30


def test_missing_all_fields_is_red():
    from app.services.extractor import extract_fields
    result = extract_fields("")
    risk_score, badge, flags, shap = score(result, "low")
    assert badge == "red"
    assert risk_score >= 70


def test_low_confidence_adds_risk():
    r_high = ExtractionResult(hs_code="6104.43.00", invoice_value="USD 100.00",
                               container_id="ABCD1234567", importer="PT A")
    r_low  = ExtractionResult(hs_code="6104.43.00", invoice_value="USD 100.00",
                               container_id="ABCD1234567", importer="PT A")
    score_high, _, _, _ = score(r_high, "high")
    score_low,  _, _, _ = score(r_low,  "low")
    assert score_low > score_high


def test_high_risk_hs_code_flagged():
    result = ExtractionResult(
        hs_code="8471.30.00",
        invoice_value="USD 500.00",
        container_id="ABCD1234567",
        importer="PT B",
    )
    risk_score, _, flags, shap = score(result, "high")
    assert "hs_high_scrutiny_category" in flags


def test_shap_values_returned():
    result = ExtractionResult(
        hs_code="8471.30.00",
        invoice_value="USD 12,500.00",
        container_id="TCKU1234567",
        importer="PT Maju Jaya",
        exporter="Samsung Electronics",
    )
    risk_score, badge, flags, shap = score(result, "high")
    assert isinstance(shap, list)
    if shap:  # only if XGBoost model loaded
        assert len(shap) == 16
        assert all("feature" in s and "shap_value" in s and "direction" in s for s in shap)


def test_ner_extraction_method():
    from app.services.extractor import extract_fields
    text = (
        "COMMERCIAL INVOICE  Invoice No.: INV-2026-1234\n"
        "CONSIGNEE: PT Kalbe Farma Tbk, Jakarta\n"
        "SHIPPER: Mitsubishi Electric Corporation, Tokyo\n"
        "HS Code: 8504.40.00   Total Value: USD 45,000.00\n"
        "Container No.: HLCU1234567\n"
        "Vessel: MV Pacific Star   Port of Loading: Yokohama, Japan\n"
        "Net Weight: 320.50 KG   Gross Weight: 350.00 KG"
    )
    result = extract_fields(text)
    assert result.hs_code == "8504.40.00"
    assert result.importer is not None and "Kalbe" in result.importer
    assert result.container_id == "HLCU1234567"
    assert result.invoice_value is not None
    assert result.extraction_method in ("ner", "ner+regex", "regex")
