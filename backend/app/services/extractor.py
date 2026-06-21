import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExtractionResult:
    hs_code: Optional[str] = None
    invoice_value: Optional[str] = None
    container_id: Optional[str] = None
    importer: Optional[str] = None
    exporter: Optional[str] = None
    net_weight: Optional[str] = None
    gross_weight: Optional[str] = None
    vessel_name: Optional[str] = None
    port_of_origin: Optional[str] = None
    invoice_number: Optional[str] = None
    carton_count: Optional[str] = None
    missing_critical: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "missing_critical"}


# Field extraction patterns
_PATTERNS = {
    "hs_code": re.compile(r"\b(\d{4}\.\d{2}\.\d{2,4})\b"),
    "container_id": re.compile(r"\b([A-Z]{4}\d{7})\b"),
    "invoice_value": re.compile(
        r"(USD|EUR|SGD|CNY|IDR|JPY)\s*([\d,]+(?:\.\d{2})?)",
        re.IGNORECASE,
    ),
    "invoice_number": re.compile(
        r"(?:invoice\s*no\.?|inv\.?\s*no\.?|invoice\s*#)\s*([A-Z0-9\-\/]+)",
        re.IGNORECASE,
    ),
    "net_weight": re.compile(
        r"(?:net\s*weight|n\.?w\.?)\s*[:\-]?\s*([\d,\.]+\s*(?:kg|kgs|mt))",
        re.IGNORECASE,
    ),
    "gross_weight": re.compile(
        r"(?:gross\s*weight|g\.?w\.?)\s*[:\-]?\s*([\d,\.]+\s*(?:kg|kgs|mt))",
        re.IGNORECASE,
    ),
    "carton_count": re.compile(
        r"(\d+)\s*(?:cartons?|ctns?|pkgs?|packages?)",
        re.IGNORECASE,
    ),
    "vessel_name": re.compile(
        r"(?:vessel\s*name|m\.?v\.?|vessel)\s*[:\-]?\s*([A-Z][A-Za-z0-9\s\-]+?)(?:\n|voyage|voy|$)",
        re.IGNORECASE,
    ),
    "port_of_origin": re.compile(
        r"(?:port\s*of\s*(?:loading|origin)|pol)\s*[:\-]?\s*([A-Za-z\s,]+?)(?:\n|port\s*of|$)",
        re.IGNORECASE,
    ),
    "importer": re.compile(
        r"(?:consignee|importer|buyer)\s*[:\-]?\s*((?:PT|CV|UD|Ltd|LLC)\.?\s*[A-Za-z\s]+?)(?:\n|$)",
        re.IGNORECASE,
    ),
    "exporter": re.compile(
        r"(?:shipper|exporter|seller)\s*[:\-]?\s*([A-Za-z][A-Za-z0-9\s,\.]+?)(?:\n|$)",
        re.IGNORECASE,
    ),
}

_CRITICAL_FIELDS = {"hs_code", "invoice_value", "container_id", "importer"}


def extract_fields(text: str) -> ExtractionResult:
    result = ExtractionResult()

    m = _PATTERNS["hs_code"].search(text)
    if m:
        result.hs_code = m.group(1)

    m = _PATTERNS["container_id"].search(text)
    if m:
        result.container_id = m.group(1)

    m = _PATTERNS["invoice_value"].search(text)
    if m:
        result.invoice_value = f"{m.group(1).upper()} {m.group(2)}"

    m = _PATTERNS["invoice_number"].search(text)
    if m:
        result.invoice_number = m.group(1).strip()

    m = _PATTERNS["net_weight"].search(text)
    if m:
        result.net_weight = m.group(1).strip()

    m = _PATTERNS["gross_weight"].search(text)
    if m:
        result.gross_weight = m.group(1).strip()

    m = _PATTERNS["carton_count"].search(text)
    if m:
        result.carton_count = m.group(1).strip()

    m = _PATTERNS["vessel_name"].search(text)
    if m:
        result.vessel_name = m.group(1).strip()

    m = _PATTERNS["port_of_origin"].search(text)
    if m:
        result.port_of_origin = m.group(1).strip()

    m = _PATTERNS["importer"].search(text)
    if m:
        result.importer = m.group(1).strip()

    m = _PATTERNS["exporter"].search(text)
    if m:
        result.exporter = m.group(1).strip()

    result.missing_critical = [
        f for f in _CRITICAL_FIELDS if getattr(result, f) is None
    ]

    return result
