"""
Field extractor — two-stage NLP pipeline.

Stage 1: spaCy NER model (deep learning) — primary extractor.
         Understands context: "Consignee", "Penerima", "To:" all map to IMPORTER.

Stage 2: Regex fallback — catches anything NER missed.
         Runs on unextracted fields only so the two stages complement each other.

Model: models/ner_model/  (trained on 300 customs document examples)
"""
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Data model ────────────────────────────────────────────────────────────────

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
    extraction_method: str = "regex"       # "ner" | "ner+regex" | "regex"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()
                if k not in ("missing_critical", "extraction_method")}


# ── NER label → result field mapping ─────────────────────────────────────────
_LABEL_MAP = {
    "HS_CODE":        "hs_code",
    "INVOICE_VALUE":  "invoice_value",
    "CONTAINER_ID":   "container_id",
    "IMPORTER":       "importer",
    "EXPORTER":       "exporter",
    "NET_WEIGHT":     "net_weight",
    "GROSS_WEIGHT":   "gross_weight",
    "VESSEL_NAME":    "vessel_name",
    "PORT_OF_ORIGIN": "port_of_origin",
    "INVOICE_NUMBER": "invoice_number",
    "CARTON_COUNT":   "carton_count",
}

_CRITICAL_FIELDS = {"hs_code", "invoice_value", "container_id", "importer"}

# ── Load NER model once ───────────────────────────────────────────────────────
_NER = None
_NER_PATH = Path(__file__).parent.parent.parent / "models" / "ner_model"


def _load_ner():
    global _NER
    if _NER is not None:
        return _NER
    try:
        import spacy
        _NER = spacy.load(str(_NER_PATH))
        logger.info("spaCy NER model loaded from %s", _NER_PATH)
    except Exception as e:
        logger.warning("spaCy NER not loaded (%s) — regex-only mode", e)
        _NER = False
    return _NER


# ── Regex fallback patterns ───────────────────────────────────────────────────
_PATTERNS = {
    "hs_code": re.compile(r"\b(\d{4}\.\d{2}\.\d{2,4})\b"),
    "container_id": re.compile(r"\b([A-Z]{4}\d{7})\b"),
    "invoice_value": re.compile(
        r"(?:total|amount|value|nilai)[^\n]{0,30}?(USD|EUR|SGD|CNY|IDR|JPY)\s*([\d,]+(?:\.\d{2})?)"
        r"|(?:^|\n)(USD|EUR|SGD|CNY|IDR|JPY)\s+([\d,]+(?:\.\d{2})?)",
        re.IGNORECASE | re.MULTILINE),
    "invoice_number": re.compile(
        r"(?:invoice\s*no\.?|inv\.?\s*no\.?|invoice\s*#|no\.\s*faktur)\s*[:\-]?\s*([A-Z0-9\-\/]+)",
        re.IGNORECASE),
    "net_weight": re.compile(
        r"(?:net\s*weight|n\.?w\.?|berat\s*bersih)\s*[:\-]?\s*([\d,\.]+\s*(?:kg|kgs|mt)?)"
        r"|(?:net\s*weight\s*\(kg\)[^\n]*\n(?:[^\n]*\n){0,5}?(?:tota[l\s]+)?)([\d,\.]+)",
        re.IGNORECASE),
    "gross_weight": re.compile(
        r"(?:gross\s*weight|g\.?w\.?|berat\s*kotor)\s*[:\-]?\s*([\d,\.]+\s*(?:kg|kgs|mt))",
        re.IGNORECASE),
    "carton_count": re.compile(
        r"(\d+)\s*(?:cartons?|ctns?|pkgs?|packages?|koli|karton)", re.IGNORECASE),
    "vessel_name": re.compile(
        r"(?:vessel\s*(?:name)?|kapal)\s*(?:/\s*\w+)?\s*[:\-]?\s*\n?\s*(MV\s+[A-Za-z0-9\s\-]+?)(?:\n|voyage|voy|$)"
        r"|(?:^|\s)(MV\s+[A-Z][A-Za-z0-9\s\-]{3,30}?)(?:\n|voyage|voy|Voy|\s{2,}|$)",
        re.IGNORECASE | re.MULTILINE),
    "port_of_origin": re.compile(
        r"(?:port\s*of\s*(?:loading|origin)|pol|pelabuhan\s*(?:muat|asal))\s*[:\-]?\s*([A-Za-z\s,]+?)(?:\n|port\s*of|$)",
        re.IGNORECASE),
    "importer": re.compile(
        r"(?:consignee|importer|buyer|penerima)(?:\s*/\s*\w+)?\s*[:\-]?\s*\n?"
        r"(?:[^\n]*\n){0,6}?\s*((?:PT|CV|UD|Ltd|LLC)\.?\s*[A-Za-z\s]+?)(?:\n|$)",
        re.IGNORECASE),
    "exporter": re.compile(
        r"(?:shipper|exporter|seller|pengirim)\s*[:\-]?\s*([A-Za-z][A-Za-z0-9\s,\.]+?)(?:\n|$)",
        re.IGNORECASE),
}


def _regex_extract(text: str, result: ExtractionResult) -> ExtractionResult:
    """Fill any None fields using regex patterns."""
    if not result.hs_code:
        m = _PATTERNS["hs_code"].search(text)
        if m: result.hs_code = m.group(1)

    if not result.container_id:
        m = _PATTERNS["container_id"].search(text)
        if m: result.container_id = m.group(1)

    if not result.invoice_value:
        m = _PATTERNS["invoice_value"].search(text)
        if m:
            # Pattern has two alternatives: groups (1,2) for "total...USD X" or (3,4) for "USD X" on own line
            if m.group(1) and m.group(2):
                result.invoice_value = f"{m.group(1).upper()} {m.group(2)}"
            elif m.group(3) and m.group(4):
                result.invoice_value = f"{m.group(3).upper()} {m.group(4)}"

    if not result.invoice_number:
        m = _PATTERNS["invoice_number"].search(text)
        if m: result.invoice_number = m.group(1).strip()

    if not result.net_weight:
        m = _PATTERNS["net_weight"].search(text)
        if m:
            val = (m.group(1) or m.group(2) or "").strip()
            if val:
                result.net_weight = val if "kg" in val.lower() else f"{val} KG"
        else:
            # Packing list TOTAL row: "TOTAL [cartons] [net] [gross] [cbm]"
            import re as _re
            tot = _re.search(
                r'(?:TOTA[L\s]*|total)\s+\d+\s+([\d,\.]+)\s+([\d,\.]+)',
                text, _re.IGNORECASE)
            if tot and result.gross_weight is None:
                result.net_weight   = f"{tot.group(1)} KG"
                result.gross_weight = f"{tot.group(2)} KG"

    if not result.gross_weight:
        m = _PATTERNS["gross_weight"].search(text)
        if m: result.gross_weight = m.group(1).strip()

    if not result.carton_count:
        m = _PATTERNS["carton_count"].search(text)
        if m: result.carton_count = m.group(1).strip()

    if not result.vessel_name:
        m = _PATTERNS["vessel_name"].search(text)
        if m:
            result.vessel_name = (m.group(1) or m.group(2) or "").strip()
        else:
            # Direct MV pattern — catches "MV Pacific Star", "MV Cosco Harmony" etc.
            import re as _re
            mv = _re.search(r'\bMV\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})', text)
            if mv:
                result.vessel_name = f"MV {mv.group(1).strip()}"

    if not result.port_of_origin:
        m = _PATTERNS["port_of_origin"].search(text)
        if m: result.port_of_origin = m.group(1).strip()

    if not result.importer:
        m = _PATTERNS["importer"].search(text)
        if m:
            result.importer = m.group(1).strip()
        else:
            # OCR table merge: "ExporterName PT ImporterName" on same line
            # Catches: "Apple Inc. PT ...", "Toyota Motor Corporation PT ...", "BASF SE PT ..."
            import re as _re
            m2 = _re.search(
                r'(?:Inc\.|Ltd\.|Co\.|Corp(?:oration)?\.?|GmbH|AG|SE|plc|LLC|NV|BV)'
                r'[,\s]+?((?:PT|CV|UD)\s+[A-Za-z][A-Za-z\s]{3,}?)(?:\n|$)',
                text, _re.IGNORECASE)
            if m2:
                result.importer = m2.group(1).strip()
            else:
                # Last resort: find any PT company on its own line
                m3 = _re.search(r'(?:^|\n)(PT\s+[A-Z][A-Za-z\s]{3,}?)(?:\n|$)', text)
                if m3:
                    result.importer = m3.group(1).strip()

    if not result.exporter:
        m = _PATTERNS["exporter"].search(text)
        if m: result.exporter = m.group(1).strip()

    return result


# ── Main extraction function ──────────────────────────────────────────────────

def extract_fields(text: str) -> ExtractionResult:
    """
    Extract customs fields from OCR text using NER + regex fallback.

    NER model runs first (deep learning, context-aware).
    Regex fills any fields NER missed.
    """
    result = ExtractionResult()
    ner = _load_ner()

    # ── Stage 1: spaCy NER ──────────────────────────────────────────────────
    if ner:
        try:
            doc = ner(text[:100_000])  # cap at 100k chars
            ner_found = 0
            for ent in doc.ents:
                field_name = _LABEL_MAP.get(ent.label_)
                if field_name and getattr(result, field_name) is None:
                    setattr(result, field_name, ent.text.strip())
                    ner_found += 1
            result.extraction_method = "ner"
            logger.debug("NER extracted %d fields", ner_found)
        except Exception as e:
            logger.warning("NER inference failed (%s) — regex fallback", e)

    # ── Validate NER results — discard values that look wrong ───────────────
    import re as _re

    # invoice_value: must have digits AND a currency code, reject multi-number strings
    if result.invoice_value:
        iv = result.invoice_value.strip()
        has_currency = bool(_re.search(r'USD|EUR|SGD|CNY|IDR|JPY', iv, _re.IGNORECASE))
        has_digit    = bool(_re.search(r'\d', iv))
        multi_num    = len(_re.findall(r'\d+\.\d+', iv)) > 1  # e.g. "658.07 30.968"
        if not has_digit or multi_num or not has_currency:
            result.invoice_value = None

    # container_id must be exactly 4 uppercase letters + 7 digits
    if result.container_id:
        if not _re.fullmatch(r'[A-Z]{4}\d{7}', result.container_id):
            result.container_id = None

    # net_weight / gross_weight must be a plain number optionally followed by KG/MT
    # Reject dates like "11 April", text strings, etc.
    for wfield in ("net_weight", "gross_weight"):
        val = getattr(result, wfield)
        if val:
            clean = val.strip()
            # Must start with a digit and contain only digits, commas, dots, spaces, KG/MT
            if not _re.match(r'^[\d,\.]+', clean):
                setattr(result, wfield, None)
            # Reject if it contains letters other than KG/MT/G
            elif _re.search(r'[A-Za-z]', clean) and not _re.search(r'\d+[\s,\.]*(?:kg|kgs|mt|g)\b', clean, _re.IGNORECASE):
                setattr(result, wfield, None)

    # vessel_name must not be a single word and must not be all caps label noise
    if result.vessel_name:
        vn = result.vessel_name.strip()
        if len(vn) < 4 or vn.upper() in {"VESSEL", "KAPAL", "VESSEL NAME"}:
            result.vessel_name = None

    # importer / exporter must be at least 4 chars and not a header label
    _NOISE = {"shipper", "exporter", "seller", "consignee", "importer", "buyer",
              "pengirim", "penerima", "notify", "party", "from", "to"}
    for fld in ("importer", "exporter"):
        val = getattr(result, fld)
        if val and (len(val.strip()) < 4 or val.strip().lower() in _NOISE):
            setattr(result, fld, None)

    # ── Stage 2: Regex fallback for any remaining None fields ───────────────
    missing_before = sum(1 for f in _LABEL_MAP.values() if getattr(result, f) is None)
    result = _regex_extract(text, result)
    missing_after = sum(1 for f in _LABEL_MAP.values() if getattr(result, f) is None)

    if missing_before > missing_after:
        result.extraction_method = "ner+regex" if ner else "regex"

    # ── Mark critical missing fields ────────────────────────────────────────
    result.missing_critical = [f for f in _CRITICAL_FIELDS if getattr(result, f) is None]

    return result
