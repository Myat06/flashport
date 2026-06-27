import pytest
from app.services.extractor import extract_fields

INVOICE_TEXT = """
COMMERCIAL INVOICE
Invoice No.: INV-2026-0042
Shipper: Samsung Electronics Co., Ltd
Consignee: PT Maju Jaya Indonesia

HS Code: 8471.30.00
Total Value: USD 12,500.00
Container ID: TCKU1234567
Vessel Name: MV Pacific Star
Port of Loading: Busan, Korea
Net Weight: 450 KG
Gross Weight: 520 KG
4 Cartons
"""

# Minimal field_defs that mirror the 11 built-in seed values (for unit tests — no DB required)
FIELD_DEFS = [
    {"field_key": "hs_code",        "display_label": "HS Code",        "priority": "critical",  "extraction_keywords": "HS Code,Pos Tarif,Kode Tarif", "risk_weight": 20},
    {"field_key": "importer",       "display_label": "Importer",       "priority": "critical",  "extraction_keywords": "Importer,Consignee,Penerima",   "risk_weight": 15},
    {"field_key": "invoice_value",  "display_label": "Invoice Value",  "priority": "critical",  "extraction_keywords": "Invoice Value,Total Value,Amount","risk_weight": 10},
    {"field_key": "container_id",   "display_label": "Container ID",   "priority": "critical",  "extraction_keywords": "Container No,Container ID",       "risk_weight": 10},
    {"field_key": "exporter",       "display_label": "Exporter",       "priority": "important", "extraction_keywords": "Exporter,Shipper,Pengirim",       "risk_weight":  8},
    {"field_key": "net_weight",     "display_label": "Net Weight",     "priority": "important", "extraction_keywords": "Net Weight,Nett Weight,Berat Bersih","risk_weight": 5},
    {"field_key": "gross_weight",   "display_label": "Gross Weight",   "priority": "important", "extraction_keywords": "Gross Weight,Berat Kotor",        "risk_weight":  5},
    {"field_key": "invoice_number", "display_label": "Invoice Number", "priority": "important", "extraction_keywords": "Invoice No,Invoice Number",       "risk_weight":  5},
    {"field_key": "carton_count",   "display_label": "Carton Count",   "priority": "optional",  "extraction_keywords": "Carton,Cartons,CTN,Koli",         "risk_weight":  3},
    {"field_key": "vessel_name",    "display_label": "Vessel Name",    "priority": "optional",  "extraction_keywords": "Vessel,Ship,Vessel Name,M/V,MV",  "risk_weight":  2},
    {"field_key": "port_of_origin", "display_label": "Port of Origin", "priority": "optional",  "extraction_keywords": "Port of Loading,Port of Origin,POL","risk_weight": 2},
]


def test_hs_code_extraction():
    result = extract_fields(INVOICE_TEXT, FIELD_DEFS)
    assert result.hs_code == "8471.30.00"


def test_container_id_extraction():
    result = extract_fields(INVOICE_TEXT, FIELD_DEFS)
    assert result.container_id == "TCKU1234567"


def test_invoice_value_extraction():
    result = extract_fields(INVOICE_TEXT, FIELD_DEFS)
    assert result.invoice_value == "USD 12,500.00"


def test_importer_extraction():
    result = extract_fields(INVOICE_TEXT, FIELD_DEFS)
    assert result.importer is not None
    assert "Maju Jaya" in result.importer


def test_vessel_name():
    result = extract_fields(INVOICE_TEXT, FIELD_DEFS)
    assert result.vessel_name is not None
    assert "Pacific Star" in result.vessel_name


def test_weights():
    result = extract_fields(INVOICE_TEXT, FIELD_DEFS)
    assert "450" in (result.net_weight or "")
    assert "520" in (result.gross_weight or "")


def test_no_missing_critical_when_all_present():
    result = extract_fields(INVOICE_TEXT, FIELD_DEFS)
    assert len(result.missing_critical) == 0


def test_missing_critical_on_empty_text():
    result = extract_fields("", FIELD_DEFS)
    assert "hs_code" in result.missing_critical
    assert "invoice_value" in result.missing_critical
    assert "container_id" in result.missing_critical
    assert "importer" in result.missing_critical
