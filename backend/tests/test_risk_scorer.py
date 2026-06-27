from app.services.extractor import ExtractionResult, extract_fields
from app.services.risk_scorer import score

FIELD_DEFS = [
    {"field_key": "hs_code",       "display_label": "HS Code",       "priority": "critical",  "extraction_keywords": "HS Code,Pos Tarif",          "risk_weight": 20},
    {"field_key": "importer",      "display_label": "Importer",      "priority": "critical",  "extraction_keywords": "Importer,Consignee,Penerima", "risk_weight": 15},
    {"field_key": "invoice_value", "display_label": "Invoice Value", "priority": "critical",  "extraction_keywords": "Invoice Value,Total Value",   "risk_weight": 10},
    {"field_key": "container_id",  "display_label": "Container ID",  "priority": "critical",  "extraction_keywords": "Container No,Container ID",   "risk_weight": 10},
    {"field_key": "exporter",      "display_label": "Exporter",      "priority": "important", "extraction_keywords": "Exporter,Shipper",            "risk_weight":  8},
    {"field_key": "net_weight",    "display_label": "Net Weight",    "priority": "important", "extraction_keywords": "Net Weight",                  "risk_weight":  5},
    {"field_key": "gross_weight",  "display_label": "Gross Weight",  "priority": "important", "extraction_keywords": "Gross Weight",                "risk_weight":  5},
    {"field_key": "invoice_number","display_label": "Invoice Number","priority": "important", "extraction_keywords": "Invoice No",                  "risk_weight":  5},
    {"field_key": "carton_count",  "display_label": "Carton Count",  "priority": "optional",  "extraction_keywords": "Carton,CTN",                  "risk_weight":  3},
    {"field_key": "vessel_name",   "display_label": "Vessel Name",   "priority": "optional",  "extraction_keywords": "Vessel,MV",                   "risk_weight":  2},
    {"field_key": "port_of_origin","display_label": "Port of Origin","priority": "optional",  "extraction_keywords": "Port of Loading,POL",         "risk_weight":  2},
]


def _er(**kwargs):
    """Helper: build ExtractionResult from keyword fields."""
    return ExtractionResult(fields=kwargs)


def test_clean_declaration_is_green():
    result = _er(
        hs_code="6104.43.00",
        invoice_value="USD 3,000.00",
        container_id="MSCU9876543",
        importer="PT Bersama Maju",
    )
    risk_score, badge, flags, shap = score(result, "high", FIELD_DEFS)
    assert badge == "green"
    assert risk_score < 30


def test_missing_all_fields_is_red():
    result = extract_fields("", FIELD_DEFS)
    risk_score, badge, flags, shap = score(result, "low", FIELD_DEFS)
    assert badge == "red"
    assert risk_score >= 70


def test_low_confidence_adds_risk():
    r_high = _er(hs_code="6104.43.00", invoice_value="USD 100.00",
                 container_id="ABCD1234567", importer="PT A")
    r_low  = _er(hs_code="6104.43.00", invoice_value="USD 100.00",
                 container_id="ABCD1234567", importer="PT A")
    score_high, _, _, _ = score(r_high, "high", FIELD_DEFS)
    score_low,  _, _, _ = score(r_low,  "low",  FIELD_DEFS)
    assert score_low > score_high


def test_high_risk_hs_code_flagged():
    result = _er(
        hs_code="8471.30.00",
        invoice_value="USD 500.00",
        container_id="ABCD1234567",
        importer="PT B",
    )
    risk_score, _, flags, shap = score(result, "high", FIELD_DEFS)
    assert "hs_high_scrutiny_category" in flags


def test_shap_values_returned():
    result = _er(
        hs_code="8471.30.00",
        invoice_value="USD 12,500.00",
        container_id="TCKU1234567",
        importer="PT Maju Jaya",
        exporter="Samsung Electronics",
    )
    risk_score, badge, flags, shap = score(result, "high", FIELD_DEFS)
    assert isinstance(shap, list)
    if shap:  # only if XGBoost model loaded
        assert len(shap) == 16
        assert all("feature" in s and "shap_value" in s and "direction" in s for s in shap)


def test_ner_extraction_method():
    text = (
        "COMMERCIAL INVOICE  Invoice No.: INV-2026-1234\n"
        "CONSIGNEE: PT Kalbe Farma Tbk, Jakarta\n"
        "SHIPPER: Mitsubishi Electric Corporation, Tokyo\n"
        "HS Code: 8504.40.00   Total Value: USD 45,000.00\n"
        "Container No.: HLCU1234567\n"
        "Vessel: MV Pacific Star   Port of Loading: Yokohama, Japan\n"
        "Net Weight: 320.50 KG   Gross Weight: 350.00 KG"
    )
    result = extract_fields(text, FIELD_DEFS)
    assert result.hs_code == "8504.40.00"
    assert result.importer is not None and "Kalbe" in result.importer
    assert result.container_id == "HLCU1234567"
    assert result.invoice_value is not None
    assert result.extraction_method in ("ner", "ner+regex", "regex", "keyword", "keyword+regex")
