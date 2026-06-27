"""
Field extractor — data-driven pipeline.

Stage 1: spaCy NER (trained model) — fast, context-aware for the 11 known entity types.
Stage 2: Keyword proximity extraction — for ALL active field_definitions (admin-configurable).
         Searches each line of OCR text for keyword synonyms defined in the DB.
Stage 3: Regex fallback — for built-in fields only; high-precision patterns for tricky formats.

Adding new fields: admin creates a row in field_definitions with comma-separated
extraction_keywords. No code change required.
"""
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# ── NER label → field_key mapping (trained entity types) ─────────────────────
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

# ── NER model ─────────────────────────────────────────────────────────────────
_NER = None
_NER_PATH = Path(__file__).parent.parent.parent / "models" / "ner_model"


def _load_ner():
    global _NER
    if _NER is not None:
        return _NER
    try:
        import spacy
        _NER = spacy.load(str(_NER_PATH))
        logger.info("spaCy NER loaded from %s", _NER_PATH)
    except Exception as e:
        logger.warning("spaCy NER not loaded (%s) — keyword+regex mode", e)
        _NER = False
    return _NER


# ── Dynamic ExtractionResult ─────────────────────────────────────────────────

class ExtractionResult:
    """Dict-backed result that also supports attribute access (result.hs_code).

    Maintains backward compatibility with code that uses getattr/setattr.
    """

    def __init__(self, fields=None, missing_critical=None, extraction_method="regex"):
        object.__setattr__(self, "_fields", dict(fields or {}))
        object.__setattr__(self, "missing_critical", missing_critical or [])
        object.__setattr__(self, "extraction_method", extraction_method)

    def __getattr__(self, name):
        return object.__getattribute__(self, "_fields").get(name)

    def __setattr__(self, name, value):
        if name in ("_fields", "missing_critical", "extraction_method"):
            object.__setattr__(self, name, value)
        else:
            object.__getattribute__(self, "_fields")[name] = value

    def get(self, key, default=None):
        return object.__getattribute__(self, "_fields").get(key, default)

    def items(self):
        return object.__getattribute__(self, "_fields").items()

    def keys(self):
        return object.__getattribute__(self, "_fields").keys()

    def to_dict(self):
        return dict(object.__getattribute__(self, "_fields"))


# ── Keyword proximity extraction ──────────────────────────────────────────────

def _keyword_extract(text: str, keywords: list[str]) -> str | None:
    """Find the value that follows any of the given keywords in OCR text.

    Handles patterns:
      "HS Code: 8471.30.10"          → "8471.30.10"
      "Pos Tarif — 8471.30.10"       → "8471.30.10"
      "Net Weight\\n125.5 KG"        → "125.5 KG"
    """
    if not keywords:
        return None

    lines = text.split("\n")
    kws_lower = [k.lower().strip() for k in keywords if k.strip()]

    for i, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue
        line_lower = line.lower()

        for kw in kws_lower:
            idx = line_lower.find(kw)
            if idx == -1:
                continue
            # Word-boundary check: kw must not be preceded by a letter
            if idx > 0 and line_lower[idx - 1].isalpha():
                continue

            after = line[idx + len(kw):].strip()
            # Strip leading punctuation/separators
            after = re.sub(r"^[\s:;\-–—/]+", "", after).strip()

            if after and len(after) >= 2:
                return after[:200]

            # Value may be on the next non-empty, non-label line
            for j in range(i + 1, min(i + 3, len(lines))):
                nxt = lines[j].strip()
                if not nxt:
                    continue
                # Skip if next line looks like another label (keyword in it)
                if any(k in nxt.lower() for k in kws_lower):
                    break
                return nxt[:200]

    return None


# ── Regex fallback patterns (high-precision, for built-in fields only) ───────

_PATTERNS: dict[str, re.Pattern] = {
    "hs_code": re.compile(r"\b(\d{4}\.\d{2}\.\d{2,4})\b"),
    "container_id": re.compile(r"\b([A-Z]{4}\d{7})\b"),
    "invoice_value": re.compile(
        r"(?:total|amount|value|nilai)[^\n]{0,30}?(USD|EUR|SGD|CNY|IDR|JPY)\s*([\d,]+(?:\.\d{2})?)"
        r"|(?:^|\n)(USD|EUR|SGD|CNY|IDR|JPY)\s+([\d,]+(?:\.\d{2})?)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "invoice_number": re.compile(
        r"(?:invoice\s*no\.?|inv\.?\s*no\.?|invoice\s*#|no\.\s*faktur)\s*[:\-]?\s*([A-Z0-9\-\/]+)",
        re.IGNORECASE,
    ),
    "net_weight": re.compile(
        r"(?:net\s*weight|n\.?w\.?|berat\s*bersih)\s*[:\-]?\s*([\d,\.]+\s*(?:kg|kgs|mt)?)"
        r"|(?:net\s*weight\s*\(kg\)[^\n]*\n(?:[^\n]*\n){0,5}?(?:tota[l\s]+)?)([\d,\.]+)",
        re.IGNORECASE,
    ),
    "gross_weight": re.compile(
        r"(?:gross\s*weight|g\.?w\.?|berat\s*kotor)\s*[:\-]?\s*([\d,\.]+\s*(?:kg|kgs|mt))",
        re.IGNORECASE,
    ),
    "carton_count": re.compile(
        r"(\d+)\s*(?:cartons?|ctns?|pkgs?|packages?|koli|karton)", re.IGNORECASE
    ),
    "vessel_name": re.compile(
        r"(?:vessel\s*(?:name)?|kapal)\s*(?:/\s*\w+)?\s*[:\-]?\s*\n?\s*(MV\s+[A-Za-z0-9\s\-]+?)(?:\n|voyage|voy|$)"
        r"|(?:^|\s)(MV\s+[A-Z][A-Za-z0-9\s\-]{3,30}?)(?:\n|voyage|voy|Voy|\s{2,}|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "port_of_origin": re.compile(
        r"(?:port\s*of\s*(?:loading|origin)|pol|pelabuhan\s*(?:muat|asal))\s*[:\-]?\s*([A-Za-z\s,]+?)(?:\n|port\s*of|$)",
        re.IGNORECASE,
    ),
    "importer": re.compile(
        r"(?:consignee|importer|buyer|penerima)(?:\s*/\s*\w+)?\s*[:\-]?\s*\n?"
        r"(?:[^\n]*\n){0,6}?\s*((?:PT|CV|UD|Ltd|LLC)\.?\s*[A-Za-z\s]+?)(?:\n|$)",
        re.IGNORECASE,
    ),
    "exporter": re.compile(
        r"(?:shipper|exporter|seller|pengirim)\s*[:\-]?\s*([A-Za-z][A-Za-z0-9\s,\.]+?)(?:\n|$)",
        re.IGNORECASE,
    ),
}


def _regex_fallback(text: str, result: ExtractionResult) -> None:
    """Fill built-in fields that are still None using high-precision regex patterns."""
    if not result.get("hs_code"):
        m = _PATTERNS["hs_code"].search(text)
        if m:
            result.hs_code = m.group(1)

    if not result.get("container_id"):
        m = _PATTERNS["container_id"].search(text)
        if m:
            result.container_id = m.group(1)

    if not result.get("invoice_value"):
        m = _PATTERNS["invoice_value"].search(text)
        if m:
            if m.group(1) and m.group(2):
                result.invoice_value = f"{m.group(1).upper()} {m.group(2)}"
            elif m.group(3) and m.group(4):
                result.invoice_value = f"{m.group(3).upper()} {m.group(4)}"

    if not result.get("invoice_number"):
        m = _PATTERNS["invoice_number"].search(text)
        if m:
            result.invoice_number = m.group(1).strip()

    if not result.get("net_weight"):
        m = _PATTERNS["net_weight"].search(text)
        if m:
            val = (m.group(1) or m.group(2) or "").strip()
            if val:
                result.net_weight = val if "kg" in val.lower() else f"{val} KG"
        else:
            tot = re.search(
                r"(?:TOTA[L\s]*|total)\s+\d+\s+([\d,\.]+)\s+([\d,\.]+)",
                text, re.IGNORECASE,
            )
            if tot and not result.get("gross_weight"):
                result.net_weight   = f"{tot.group(1)} KG"
                result.gross_weight = f"{tot.group(2)} KG"

    if not result.get("gross_weight"):
        m = _PATTERNS["gross_weight"].search(text)
        if m:
            result.gross_weight = m.group(1).strip()

    if not result.get("carton_count"):
        m = _PATTERNS["carton_count"].search(text)
        if m:
            result.carton_count = m.group(1).strip()

    if not result.get("vessel_name"):
        m = _PATTERNS["vessel_name"].search(text)
        if m:
            result.vessel_name = (m.group(1) or m.group(2) or "").strip()
        else:
            mv = re.search(r"\bMV\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})", text)
            if mv:
                result.vessel_name = f"MV {mv.group(1).strip()}"

    if not result.get("port_of_origin"):
        m = _PATTERNS["port_of_origin"].search(text)
        if m:
            result.port_of_origin = m.group(1).strip()

    if not result.get("importer"):
        m = _PATTERNS["importer"].search(text)
        if m:
            result.importer = m.group(1).strip()
        else:
            m2 = re.search(
                r"(?:Inc\.|Ltd\.|Co\.|Corp(?:oration)?\.?|GmbH|AG|SE|plc|LLC|NV|BV)"
                r"[,\s]+?((?:PT|CV|UD)\s+[A-Za-z][A-Za-z\s]{3,}?)(?:\n|$)",
                text, re.IGNORECASE,
            )
            if m2:
                result.importer = m2.group(1).strip()
            else:
                m3 = re.search(r"(?:^|\n)(PT\s+[A-Z][A-Za-z\s]{3,}?)(?:\n|$)", text)
                if m3:
                    result.importer = m3.group(1).strip()

    if not result.get("exporter"):
        m = _PATTERNS["exporter"].search(text)
        if m:
            result.exporter = m.group(1).strip()


# ── NER noise filters ─────────────────────────────────────────────────────────

_NOISE_LABELS = {"shipper", "exporter", "seller", "consignee", "importer",
                 "buyer", "pengirim", "penerima", "notify", "party", "from", "to"}


def _validate_ner_results(result: ExtractionResult) -> None:
    """Discard NER values that look like label noise or format errors."""
    if result.invoice_value:
        iv = result.invoice_value.strip()
        if (not re.search(r"USD|EUR|SGD|CNY|IDR|JPY", iv, re.IGNORECASE)
                or not re.search(r"\d", iv)
                or len(re.findall(r"\d+\.\d+", iv)) > 1):
            result.invoice_value = None

    if result.container_id:
        if not re.fullmatch(r"[A-Z]{4}\d{7}", result.container_id):
            result.container_id = None

    for wf in ("net_weight", "gross_weight"):
        val = result.get(wf)
        if val:
            clean = val.strip()
            if not re.match(r"^[\d,\.]+", clean):
                setattr(result, wf, None)
            elif re.search(r"[A-Za-z]", clean) and not re.search(
                r"\d+[\s,\.]*(?:kg|kgs|mt|g)\b", clean, re.IGNORECASE
            ):
                setattr(result, wf, None)

    if result.vessel_name:
        vn = result.vessel_name.strip()
        if len(vn) < 4 or vn.upper() in {"VESSEL", "KAPAL", "VESSEL NAME"}:
            result.vessel_name = None

    for fld in ("importer", "exporter"):
        val = result.get(fld)
        if val and (len(val.strip()) < 4 or val.strip().lower() in _NOISE_LABELS):
            setattr(result, fld, None)


# ── Main extraction function ──────────────────────────────────────────────────

def extract_fields(text: str, field_defs: list[dict]) -> ExtractionResult:
    """Extract fields from OCR text using three complementary stages.

    Args:
        text:       Raw Tesseract OCR output.
        field_defs: Active field definitions loaded from DB.
                    Each dict must have: field_key, priority, extraction_keywords.

    Returns:
        ExtractionResult with all found field values + metadata.
    """
    result = ExtractionResult()
    ner    = _load_ner()

    # ── Stage 1: spaCy NER ──────────────────────────────────────────────────
    if ner:
        try:
            doc      = ner(text[:100_000])
            ner_hits = 0
            for ent in doc.ents:
                fk = _LABEL_MAP.get(ent.label_)
                if fk and result.get(fk) is None:
                    result.get  # just access to confirm result exists
                    setattr(result, fk, ent.text.strip())
                    ner_hits += 1
            if ner_hits:
                result.extraction_method = "ner"
            logger.debug("NER extracted %d fields", ner_hits)
        except Exception as e:
            logger.warning("NER inference failed (%s)", e)

        _validate_ner_results(result)

    # ── Stage 2: Keyword proximity for ALL field_defs ───────────────────────
    kw_hits = 0
    for fd in field_defs:
        key      = fd["field_key"]
        kw_str   = fd.get("extraction_keywords") or ""
        keywords = [k.strip() for k in kw_str.split(",") if k.strip()]
        if not keywords or result.get(key) is not None:
            continue  # already found by NER
        value = _keyword_extract(text, keywords)
        if value:
            setattr(result, key, value)
            kw_hits += 1

    if kw_hits and result.extraction_method == "regex":
        result.extraction_method = "keyword"
    elif kw_hits:
        result.extraction_method = "ner+keyword"

    # ── Stage 3: High-precision regex fallback for built-in fields ──────────
    missing_before = sum(1 for fd in field_defs if result.get(fd["field_key"]) is None)
    _regex_fallback(text, result)
    missing_after  = sum(1 for fd in field_defs if result.get(fd["field_key"]) is None)

    if missing_before > missing_after:
        method = result.extraction_method
        if "ner" in method and "keyword" in method:
            result.extraction_method = "ner+keyword+regex"
        elif "ner" in method:
            result.extraction_method = "ner+regex"
        elif "keyword" in method:
            result.extraction_method = "keyword+regex"
        else:
            result.extraction_method = "regex"

    # ── Mark critical fields that are missing ────────────────────────────────
    result.missing_critical = [
        fd["field_key"]
        for fd in field_defs
        if fd.get("priority") == "critical" and not result.get(fd["field_key"])
    ]

    return result


# ── Bounding-box finder ───────────────────────────────────────────────────────

def find_field_bboxes(word_data: list[dict], result: ExtractionResult) -> dict[str, dict]:
    """Map extracted values back to pixel bounding boxes in the original image.

    Iterates all fields in result (dynamic), so custom admin-defined fields
    are located in the image exactly like built-in fields.
    """
    bboxes: dict[str, dict] = {}
    if not word_data:
        return bboxes

    for field_key, value in result.items():
        if not value:
            continue
        bbox = _locate_value(word_data, value)
        if bbox:
            bboxes[field_key] = bbox

    return bboxes


def _locate_value(word_data: list[dict], value: str) -> dict | None:
    """Find the tightest bounding box covering the words that form *value*."""
    clean  = re.sub(r"\s+", " ", value.strip())
    tokens = [t for t in clean.split() if len(t) >= 2][:6]
    if not tokens:
        return None

    first_up = tokens[0].upper()
    best: list[dict] | None = None
    best_score = 0

    for i, wd in enumerate(word_data):
        wt = wd["text"].upper().strip()
        if not wt:
            continue
        if first_up not in wt and wt not in first_up:
            continue

        matched = [wd]
        j = i + 1
        for tok in tokens[1:]:
            tok_up = tok.upper()
            for look in range(j, min(j + 4, len(word_data))):
                lwt = word_data[look]["text"].upper().strip()
                if tok_up in lwt or lwt in tok_up:
                    matched.append(word_data[look])
                    j = look + 1
                    break

        if len(matched) > best_score:
            best_score = len(matched)
            best = matched

    if not best:
        return None

    pad = 4
    x1 = min(w["x"] for w in best)
    y1 = min(w["y"] for w in best)
    x2 = max(w["x"] + w["w"] for w in best)
    y2 = max(w["y"] + w["h"] for w in best)
    return {
        "x": max(0, x1 - pad),
        "y": max(0, y1 - pad),
        "w": x2 - x1 + 2 * pad,
        "h": y2 - y1 + 2 * pad,
    }
