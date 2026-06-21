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


def test_hs_code_extraction():
    result = extract_fields(INVOICE_TEXT)
    assert result.hs_code == "8471.30.00"


def test_container_id_extraction():
    result = extract_fields(INVOICE_TEXT)
    assert result.container_id == "TCKU1234567"


def test_invoice_value_extraction():
    result = extract_fields(INVOICE_TEXT)
    assert result.invoice_value == "USD 12,500.00"


def test_importer_extraction():
    result = extract_fields(INVOICE_TEXT)
    assert result.importer is not None
    assert "Maju Jaya" in result.importer


def test_vessel_name():
    result = extract_fields(INVOICE_TEXT)
    assert result.vessel_name is not None
    assert "Pacific Star" in result.vessel_name


def test_weights():
    result = extract_fields(INVOICE_TEXT)
    assert "450" in (result.net_weight or "")
    assert "520" in (result.gross_weight or "")


def test_no_missing_critical_when_all_present():
    result = extract_fields(INVOICE_TEXT)
    assert len(result.missing_critical) == 0


def test_missing_critical_on_empty_text():
    result = extract_fields("")
    assert "hs_code" in result.missing_critical
    assert "invoice_value" in result.missing_critical
    assert "container_id" in result.missing_critical
    assert "importer" in result.missing_critical
