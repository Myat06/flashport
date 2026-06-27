"""
Comprehensive synthetic training data generator — FlashPort risk scorer.

Covers every realistic scenario at Cikarang Dry Port:
  • All 3 document types with their specific required fields
  • 12 scenario profiles per doc type
  • Inter-feature correlations XGBoost can learn (rules cannot)
  • Doc-type-aware labelling (BoL with no invoice_value is NOT penalised)
  • Realistic class balance: ~55% green, 30% yellow, 15% red

Output: backend/data/training_declarations.csv  (6,000 records)
"""
import csv
import math
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

random.seed(2026)

# ── Indonesian importers (Cikarang / Bekasi industrial zone) ──────────────────
IMPORTERS = [
    "PT Astra Honda Motor", "PT Toyota Motor Manufacturing Indonesia",
    "PT Unilever Indonesia", "PT Indofood Sukses Makmur", "PT Kalbe Farma",
    "PT Cikarang Listrindo", "PT Multi Bintang Indonesia", "PT Maju Jaya Abadi",
    "PT Sinar Harapan Nusantara", "PT Delta Dunia Makmur", "PT Surya Citra Media",
    "PT Cipta Karya Unggul", "PT Jababeka Infrastruktur", "PT LG Electronics Indonesia",
    "PT Samsung Electronics Indonesia", "PT Sharp Electronics Indonesia",
    "PT Panasonic Manufacturing Indonesia", "PT Mitsubishi Motors Krama Yudha",
    "PT Honda Prospect Motor", "PT Yamaha Indonesia Motor Manufacturing",
    "PT Suzuki Indomobil Motor", "PT Pertamina Lubricants", "PT Holcim Indonesia",
    "PT Krakatau Steel", "PT Charoen Pokphand Indonesia", "PT Mayora Indah",
    "PT Garudafood Putra Putri Jaya", "PT Wings Food", "PT Nestle Indonesia",
    "PT Frisian Flag Indonesia", "PT Beiersdorf Indonesia",
    "PT Procter Gamble Home Products Indonesia", "PT Reckitt Benckiser Indonesia",
    "PT 3M Indonesia", "PT Siemens Indonesia", "PT ABB Sakti Industri",
    "PT Schneider Electric Manufacturing", "PT Philips Industries Batam",
    "PT Epson Indonesia", "PT Fuji Xerox Indonesia",
    # Some ambiguous/problematic importers (should trigger higher scrutiny)
    "CV Mandiri Jaya", "UD Sejahtera Bersama", "CV Multi Global Trading",
    "PT Karya Abadi Nusantara", "PT Global Trade Solutions",
]

# ── Foreign exporters ──────────────────────────────────────────────────────────
EXPORTERS = [
    "Samsung Electronics Co., Ltd", "LG Electronics Inc.", "Hyundai Motor Company",
    "Kia Corporation", "SK Hynix Inc.", "Posco Co., Ltd", "LG Chem Ltd",
    "Foxconn Industrial Internet Co., Ltd", "Haier Group Corporation",
    "Midea Group Co., Ltd", "BYD Auto Co., Ltd", "Huawei Technologies Co., Ltd",
    "Lenovo Group Limited", "Xiaomi Corporation", "CNOOC Limited", "Sinopec Corp",
    "Toyota Motor Corporation", "Honda Motor Co., Ltd",
    "Mitsubishi Electric Corporation", "Panasonic Holdings Corporation",
    "Sony Group Corporation", "Canon Inc.", "Bridgestone Corporation",
    "Sumitomo Chemical Co., Ltd", "Toray Industries Inc.",
    "Apple Inc.", "3M Company", "Exxon Mobil Corporation",
    "Procter & Gamble Company", "Caterpillar Inc.", "Cargill Incorporated",
    "BASF SE", "Siemens AG", "Bosch GmbH", "BMW AG", "Bayer AG",
    "Royal Dutch Shell plc", "Philips N.V.", "Unilever N.V.",
]

# ── HS codes ──────────────────────────────────────────────────────────────────
HS_CODES = [
    # Electronics — moderate scrutiny
    {"code": "8471.30.00", "desc": "Laptops / portable computers",          "category": "Electronics", "value_range": (800,   150_000), "restricted": False, "risk_adj": 10},
    {"code": "8517.12.00", "desc": "Smartphones and mobile phones",         "category": "Electronics", "value_range": (200,    80_000), "restricted": False, "risk_adj": 10},
    {"code": "8528.72.00", "desc": "LCD / LED televisions",                 "category": "Electronics", "value_range": (150,    60_000), "restricted": False, "risk_adj":  8},
    {"code": "8542.31.00", "desc": "Integrated circuits / processors",      "category": "Electronics", "value_range": (500,   200_000), "restricted": False, "risk_adj": 12},
    {"code": "8443.31.00", "desc": "Printing machines",                     "category": "Electronics", "value_range": (300,    80_000), "restricted": False, "risk_adj":  5},
    {"code": "8504.40.00", "desc": "Static converters / power supply",      "category": "Electronics", "value_range": (200,    60_000), "restricted": False, "risk_adj":  5},
    {"code": "9013.80.00", "desc": "Liquid crystal devices (LCDs)",         "category": "Electronics", "value_range": (1_000, 300_000), "restricted": False, "risk_adj": 10},
    # Auto parts — low risk
    {"code": "8708.29.00", "desc": "Body parts for motor vehicles",         "category": "Auto Parts",  "value_range": (1_000,  80_000), "restricted": False, "risk_adj":  3},
    {"code": "8708.99.00", "desc": "Other parts for motor vehicles",        "category": "Auto Parts",  "value_range": (500,    50_000), "restricted": False, "risk_adj":  3},
    {"code": "4011.10.00", "desc": "Pneumatic tyres for motor cars",        "category": "Auto Parts",  "value_range": (2_000,  60_000), "restricted": False, "risk_adj":  3},
    {"code": "8407.34.00", "desc": "Reciprocating piston engines",          "category": "Machinery",   "value_range": (5_000, 200_000), "restricted": False, "risk_adj":  5},
    # Chemicals — high risk (some restricted)
    {"code": "2710.19.00", "desc": "Petroleum oils and preparations",       "category": "Chemicals",   "value_range": (10_000, 500_000),"restricted": True,  "risk_adj": 30},
    {"code": "2711.21.00", "desc": "Natural gas in gaseous state",          "category": "Chemicals",   "value_range": (20_000, 800_000),"restricted": True,  "risk_adj": 30},
    {"code": "3901.10.00", "desc": "Polyethylene density < 0.94",           "category": "Chemicals",   "value_range": (3_000,  80_000), "restricted": False, "risk_adj":  8},
    {"code": "2902.20.00", "desc": "Benzene",                               "category": "Chemicals",   "value_range": (5_000, 120_000), "restricted": True,  "risk_adj": 25},
    {"code": "3004.90.00", "desc": "Pharmaceutical preparations",           "category": "Pharma",      "value_range": (5_000, 200_000), "restricted": False, "risk_adj": 10},
    # Textiles — low risk
    {"code": "6110.20.00", "desc": "Jerseys / pullovers of cotton",         "category": "Textiles",    "value_range": (500,    30_000), "restricted": False, "risk_adj":  2},
    {"code": "6203.42.00", "desc": "Mens trousers of cotton",               "category": "Textiles",    "value_range": (300,    20_000), "restricted": False, "risk_adj":  2},
    {"code": "6204.62.00", "desc": "Womens trousers of cotton",             "category": "Textiles",    "value_range": (300,    20_000), "restricted": False, "risk_adj":  2},
    {"code": "5208.21.00", "desc": "Woven fabrics of cotton",               "category": "Textiles",    "value_range": (1_000,  40_000), "restricted": False, "risk_adj":  2},
    # Food & Beverage — low risk
    {"code": "0901.11.00", "desc": "Coffee not roasted not decaffeinated",  "category": "Food",        "value_range": (2_000,  50_000), "restricted": False, "risk_adj":  2},
    {"code": "1006.30.00", "desc": "Semi-milled or wholly milled rice",     "category": "Food",        "value_range": (1_000,  60_000), "restricted": False, "risk_adj":  3},
    {"code": "2106.90.00", "desc": "Food preparations NES",                 "category": "Food",        "value_range": (500,    20_000), "restricted": False, "risk_adj":  3},
    # Steel & Materials — moderate risk
    {"code": "7208.51.00", "desc": "Flat-rolled products of iron / steel",  "category": "Metals",      "value_range": (5_000, 200_000), "restricted": False, "risk_adj":  8},
    {"code": "7606.12.00", "desc": "Rectangular aluminium plates",          "category": "Metals",      "value_range": (3_000, 100_000), "restricted": False, "risk_adj":  6},
    # Weapons — very high risk (always restricted)
    {"code": "9301.00.00", "desc": "Military weapons",                      "category": "Weapons",     "value_range": (10_000, 800_000),"restricted": True,  "risk_adj": 50},
    {"code": "9302.00.00", "desc": "Revolvers and pistols",                 "category": "Weapons",     "value_range": (5_000, 250_000), "restricted": True,  "risk_adj": 50},
    # Machinery — low-moderate risk
    {"code": "8457.10.00", "desc": "Machining centres for working metal",   "category": "Machinery",   "value_range": (20_000, 600_000),"restricted": False, "risk_adj":  5},
    {"code": "8421.21.00", "desc": "Water filtration / purifying machinery","category": "Machinery",   "value_range": (3_000, 100_000), "restricted": False, "risk_adj":  4},
    {"code": "8477.10.00", "desc": "Injection moulding machines",           "category": "Machinery",   "value_range": (10_000, 400_000),"restricted": False, "risk_adj":  5},
    # Consumer goods
    {"code": "9401.61.00", "desc": "Seats with wooden frames",              "category": "Furniture",   "value_range": (500,    30_000), "restricted": False, "risk_adj":  2},
    {"code": "9403.20.00", "desc": "Metal furniture",                       "category": "Furniture",   "value_range": (1_000,  50_000), "restricted": False, "risk_adj":  2},
    {"code": "3401.11.00", "desc": "Soap for toilet use",                   "category": "FMCG",        "value_range": (500,    20_000), "restricted": False, "risk_adj":  2},
]

_HS_NORMAL    = [h for h in HS_CODES if not h["restricted"] and h["risk_adj"] < 10]
_HS_SCRUTINY  = [h for h in HS_CODES if h["risk_adj"] >= 10 and not h["restricted"]]
_HS_RESTRICTED = [h for h in HS_CODES if h["restricted"]]

SHIPPING_LINES = ["TCKU", "MSCU", "MAEU", "HLCU", "CMAU", "OOLU", "EVGR", "YMLU", "APHU", "KKFU"]

VESSELS = [
    "MV Maersk Seletar", "MV MSC Gaia", "MV CMA CGM Coral", "MV Evergreen Universe",
    "MV Yang Ming Wellness", "MV Hapag Jakarta Express", "MV OOCL Indonesia",
    "MV Pacific Star", "MV Asian Spirit", "MV Nusantara Express",
    "MV Jaya Kencana", "MV Sinar Bandung", "MV Bunga Teratai",
    "MV APL Singapore", "MV Cosco Harmony", "MV Wan Hai 232",
    "MV Mataram Star", "MV Meratus Palembang", "MV Tanto Aman",
    "MV MSC Vidisha R", "MV Maersk Batam", "MV CMA CGM Callisto",
]

PORTS = [
    "Busan, Korea", "Shanghai, China", "Guangzhou, China", "Shenzhen, China",
    "Tianjin, China", "Qingdao, China", "Ningbo, China",
    "Singapore", "Port Klang, Malaysia",
    "Yokohama, Japan", "Osaka, Japan", "Kobe, Japan",
    "Rotterdam, Netherlands", "Hamburg, Germany", "Antwerp, Belgium",
    "Los Angeles, USA", "Long Beach, USA",
    "Mumbai, India", "Chennai, India",
    "Bangkok, Thailand", "Ho Chi Minh City, Vietnam",
]


def _container_id():
    prefix = random.choice(SHIPPING_LINES)
    digits = "".join(str(random.randint(0, 9)) for _ in range(7))
    return f"{prefix}{digits}"


def _invoice_number():
    year   = random.choice([2025, 2026])
    num    = random.randint(1, 9999)
    prefix = random.choice(["INV", "SI", "PO", "CI", "SO", "BL"])
    return f"{prefix}-{year}-{num:04d}"


def _invoice_value(hs_meta):
    lo, hi = hs_meta["value_range"]
    return round(random.uniform(lo, hi), 2)


def _weights(cartons):
    net   = round(random.uniform(5, 50) * cartons * random.uniform(0.8, 0.95), 2)
    gross = round(net / random.uniform(0.82, 0.94), 2)
    return net, gross


def _label(rec: dict, doc_type: str, profile: str) -> str:
    """Doc-type-aware labelling aligned with the actual risk scorer.

    Guaranteed-red conditions are deterministic so the model always sees
    enough red examples. Borderline cases get realistic noise.
    """

    # ── Guaranteed RED conditions (no noise) ──────────────────────────────────
    # Restricted goods (weapons, petroleum) — always red at Indonesian customs
    if rec.get("hs_restricted") and rec.get("hs_risk_adj", 0) >= 25:
        return "red"

    # High value with no container ID on commercial invoice
    try:
        inv = float(rec.get("invoice_value_usd", 0))
    except (ValueError, TypeError):
        inv = 0.0

    if inv > 50_000 and not rec.get("container_id") and doc_type == "commercial_invoice":
        return "red"

    # 3+ critical fields missing simultaneously
    critical = {
        "commercial_invoice": ["hs_code", "invoice_value", "container_id", "importer"],
        "bill_of_lading":     ["vessel_name", "container_id", "importer"],
        "packing_list":       ["net_weight", "gross_weight", "container_id", "importer"],
    }[doc_type]
    missing_critical = sum(1 for f in critical if not rec.get(f))
    if missing_critical >= 3:
        return "red"

    # Missing importer + low OCR confidence = always red
    if not rec.get("importer") and rec["confidence_badge"] == "low":
        return "red"

    # ── Scored risk for everything else ───────────────────────────────────────
    risk = 0

    # Fields expected for ALL doc types
    if not rec["importer"]:     risk += 15
    if not rec["exporter"]:     risk += 8
    if not rec["container_id"]: risk += 10

    # Doc-type-specific required fields
    if doc_type == "commercial_invoice":
        if not rec["hs_code"]:        risk += 20
        if not rec["invoice_value"]:  risk += 10
        if not rec["invoice_number"]: risk += 5
    elif doc_type == "bill_of_lading":
        if not rec["vessel_name"]:    risk += 10
        if not rec["port_of_origin"]: risk += 8
    elif doc_type == "packing_list":
        if not rec["net_weight"]:     risk += 10
        if not rec["gross_weight"]:   risk += 8
        if not rec["carton_count"]:   risk += 5

    # OCR confidence
    risk += {"high": 0, "medium": 8, "low": 20}[rec["confidence_badge"]]

    # HS scrutiny (non-restricted but sensitive)
    hs_prefix = rec.get("hs_code", "").replace(".", "")[:4]
    if hs_prefix in {"8471", "8517", "8542", "9013"}:
        risk += 10

    # Very high value shipment
    if inv > 200_000:
        risk += 10

    # Realistic noise — keeps borderline cases interesting for the model
    risk += random.randint(-5, 8)
    risk = max(0, min(100, risk))

    if risk < 30:  return "green"
    if risk < 70:  return "yellow"
    return "red"


def _make_record(doc_type: str, profile: str) -> dict:
    """
    Profiles and what they simulate:
      clean          → perfect document, all fields, high confidence
      good_medium    → all fields, medium confidence
      optional_gap   → 1-2 optional/secondary fields missing
      missing_one    → exactly one important field missing
      missing_hs     → no HS code (CI only trigger)
      missing_importer → no importer
      missing_cont   → no container ID
      low_conf       → low OCR confidence, some gaps
      high_value     → invoice > 200k USD, with container
      high_value_nc  → invoice > 50k USD, no container
      scrutiny_hs    → high-scrutiny HS code (electronics, chemicals)
      restricted     → restricted/weapons HS code
    """
    # ── HS code selection ──────────────────────────────────────────────────────
    if profile == "restricted":
        hs = random.choice(_HS_RESTRICTED)
    elif profile == "scrutiny_hs":
        hs = random.choice(_HS_SCRUTINY + _HS_RESTRICTED[:2])
    else:
        hs = random.choice(_HS_NORMAL + _HS_SCRUTINY)

    cartons    = random.randint(1, 500)
    inv_usd    = _invoice_value(hs)
    net_kg, gross_kg = _weights(cartons)

    # Override invoice for high-value profiles
    if profile == "high_value":
        inv_usd = random.uniform(200_000, 1_500_000)
    elif profile == "high_value_nc":
        inv_usd = random.uniform(50_001, 800_000)

    conf = random.choice(["high", "high", "high", "medium"])
    if profile in ("low_conf", "missing_one", "missing_hs", "missing_importer"):
        conf = random.choice(["medium", "low"])
    if profile == "restricted":
        conf = random.choice(["medium", "medium", "low"])

    rec = {
        "scan_id":         str(uuid.uuid4()),
        "document_type":   doc_type,
        "hs_code":         hs["code"],
        "hs_description":  hs["desc"],
        "hs_category":     hs["category"],
        "hs_restricted":   hs["restricted"],
        "hs_risk_adj":     hs["risk_adj"],
        "invoice_value":   f"USD {inv_usd:,.2f}",
        "invoice_value_usd": inv_usd,
        "invoice_number":  _invoice_number(),
        "container_id":    _container_id(),
        "importer":        random.choice(IMPORTERS),
        "exporter":        random.choice(EXPORTERS),
        "net_weight":      f"{net_kg} KG",
        "gross_weight":    f"{gross_kg} KG",
        "carton_count":    str(cartons),
        "vessel_name":     random.choice(VESSELS),
        "port_of_origin":  random.choice(PORTS),
        "confidence_badge": conf,
        "scanned_at":      (
            datetime(2026, 1, 1) + timedelta(
                days=random.randint(0, 178),
                hours=random.randint(6, 22),
                minutes=random.randint(0, 59),
            )
        ).isoformat(),
        "operator_id": random.choice(["CDP-001", "CDP-002", "CDP-003"]),
    }

    # ── Apply profile-specific field blanking ──────────────────────────────────
    if profile == "optional_gap":
        # 1–2 non-critical fields missing
        pool = {
            "commercial_invoice": ["invoice_number", "exporter", "vessel_name", "port_of_origin"],
            "bill_of_lading":     ["exporter", "carton_count"],
            "packing_list":       ["invoice_number", "exporter", "vessel_name"],
        }[doc_type]
        for f in random.sample(pool, k=random.randint(1, 2)):
            rec[f] = ""

    elif profile == "missing_one":
        important = {
            "commercial_invoice": ["hs_code", "container_id", "exporter", "invoice_number"],
            "bill_of_lading":     ["vessel_name", "port_of_origin", "container_id"],
            "packing_list":       ["net_weight", "gross_weight", "container_id"],
        }[doc_type]
        rec[random.choice(important)] = ""

    elif profile == "missing_hs":
        rec["hs_code"] = ""

    elif profile == "missing_importer":
        rec["importer"] = ""
        if random.random() < 0.4:
            rec["exporter"] = ""

    elif profile == "missing_cont":
        rec["container_id"] = ""
        if random.random() < 0.3:
            rec["exporter"] = ""

    elif profile == "low_conf":
        # Low confidence + some random gaps
        pool = ["hs_code", "invoice_value", "container_id", "exporter",
                "vessel_name", "port_of_origin", "invoice_number"]
        for f in random.sample(pool, k=random.randint(1, 3)):
            rec[f] = ""
        if rec.get("invoice_value") == "":
            rec["invoice_value_usd"] = 0

    elif profile == "high_value_nc":
        rec["container_id"] = ""

    elif profile == "restricted":
        # Restricted goods: sometimes also missing fields to make it worse
        if random.random() < 0.5:
            rec["container_id"] = ""
        if random.random() < 0.3:
            rec["importer"] = ""

    # ── Missing field count ────────────────────────────────────────────────────
    critical_fields = ["hs_code", "invoice_value", "container_id",
                       "importer", "exporter", "vessel_name", "port_of_origin"]
    rec["missing_field_count"] = sum(1 for f in critical_fields if not rec.get(f))

    # ── Label ──────────────────────────────────────────────────────────────────
    rec["jalur"]       = _label(rec, doc_type, profile)
    rec["jalur_label"] = {"green": 0, "yellow": 1, "red": 2}[rec["jalur"]]

    return rec


# ── Profile distribution per doc type ─────────────────────────────────────────
#
# Realistic port throughput (Cikarang Dry Port annual ~600k TEU):
#   ~55% routine clearance → green
#   ~30% needs review     → yellow
#   ~15% flagged          → red
#
# Profiles weighted to produce that distribution after labelling noise.

_PROFILES: dict[str, dict[str, float]] = {
    # Target: ~55% green, ~30% yellow, ~15% red
    "commercial_invoice": {
        "clean":            0.22,   # → green
        "good_medium":      0.12,   # → green
        "optional_gap":     0.10,   # → green/yellow
        "missing_one":      0.10,   # → yellow
        "missing_hs":       0.09,   # → yellow/red
        "missing_importer": 0.08,   # → yellow/red
        "missing_cont":     0.08,   # → yellow
        "low_conf":         0.08,   # → yellow/red
        "high_value":       0.05,   # → yellow
        "high_value_nc":    0.05,   # → red (guaranteed)
        "scrutiny_hs":      0.02,   # → yellow/red
        "restricted":       0.01,   # → red (guaranteed)
    },
    "bill_of_lading": {
        "clean":            0.24,
        "good_medium":      0.14,
        "optional_gap":     0.10,
        "missing_one":      0.12,   # vessel or port → yellow/red
        "missing_importer": 0.10,
        "missing_cont":     0.10,
        "low_conf":         0.10,
        "high_value":       0.03,
        "high_value_nc":    0.04,   # → red (guaranteed)
        "scrutiny_hs":      0.02,
        "restricted":       0.01,   # → red (guaranteed)
        "missing_hs":       0.00,
    },
    "packing_list": {
        "clean":            0.23,
        "good_medium":      0.13,
        "optional_gap":     0.10,
        "missing_one":      0.12,   # weights or cartons
        "missing_importer": 0.10,
        "missing_cont":     0.09,
        "low_conf":         0.09,
        "high_value":       0.04,
        "high_value_nc":    0.05,   # → red (guaranteed)
        "scrutiny_hs":      0.03,
        "restricted":       0.01,   # → red (guaranteed)
        "missing_hs":       0.01,
    },
}


def generate(n_per_doc_type: int = 2000) -> list[dict]:
    records = []
    doc_types = ["commercial_invoice", "bill_of_lading", "packing_list"]

    for doc_type in doc_types:
        weights_map = _PROFILES[doc_type]
        profiles    = [p for p, w in weights_map.items() if w > 0]
        weights     = [weights_map[p] for p in profiles]

        chosen = random.choices(profiles, weights=weights, k=n_per_doc_type)
        for profile in chosen:
            records.append(_make_record(doc_type, profile))

    random.shuffle(records)
    return records


CSV_FIELDS = [
    "scan_id", "document_type", "hs_code", "hs_description", "hs_category", "hs_restricted",
    "invoice_value", "invoice_value_usd", "invoice_number",
    "container_id", "importer", "exporter",
    "net_weight", "gross_weight", "carton_count",
    "vessel_name", "port_of_origin",
    "confidence_badge", "missing_field_count",
    "scanned_at", "operator_id",
    "jalur", "jalur_label",
]


if __name__ == "__main__":
    from collections import Counter

    out = Path(__file__).parent.parent / "data" / "training_declarations.csv"
    out.parent.mkdir(exist_ok=True)

    records = generate(n_per_doc_type=2000)

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    jalur_dist = Counter(r["jalur"]       for r in records)
    doc_dist   = Counter(r["document_type"] for r in records)

    print(f"\nGenerated {len(records):,} records → {out}")
    print(f"\nLabel distribution:")
    for label in ["green", "yellow", "red"]:
        n   = jalur_dist[label]
        pct = n / len(records) * 100
        bar = "█" * int(pct / 2)
        print(f"  {label:6}  {n:4d}  ({pct:4.1f}%)  {bar}")

    print(f"\nDoc type distribution:")
    for dt, n in doc_dist.items():
        print(f"  {dt:22}  {n:4d}")

    print(f"\nSample records (one per label):")
    seen = set()
    for r in records:
        j = r["jalur"]
        if j not in seen:
            print(f"  [{j.upper():6}] {r['document_type']:22} HS={r['hs_code'] or 'MISSING':12} "
                  f"conf={r['confidence_badge']:6} val={r['invoice_value'][:14] or 'MISSING'}")
            seen.add(j)
        if len(seen) == 3:
            break
