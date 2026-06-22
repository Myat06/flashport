"""
Synthetic training data generator for FlashPort risk scorer.

Generates realistic Cikarang Dry Port-style customs declarations
covering Commercial Invoice, Bill of Lading, and Packing List.

Output: backend/data/training_declarations.csv
"""
import csv
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

# ── Indonesian importers (Bekasi / Cikarang industrial zone companies) ─────────
IMPORTERS = [
    "PT Astra Honda Motor",
    "PT Toyota Motor Manufacturing Indonesia",
    "PT Unilever Indonesia",
    "PT Indofood Sukses Makmur",
    "PT Kalbe Farma",
    "PT Cikarang Listrindo",
    "PT Multi Bintang Indonesia",
    "PT Maju Jaya Abadi",
    "PT Sinar Harapan Nusantara",
    "PT Delta Dunia Makmur",
    "PT Surya Citra Media",
    "PT Cipta Karya Unggul",
    "PT Jababeka Infrastruktur",
    "PT LG Electronics Indonesia",
    "PT Samsung Electronics Indonesia",
    "PT Sharp Electronics Indonesia",
    "PT Panasonic Manufacturing Indonesia",
    "PT Mitsubishi Motors Krama Yudha",
    "PT Honda Prospect Motor",
    "PT Yamaha Indonesia Motor Manufacturing",
    "PT Suzuki Indomobil Motor",
    "PT Pertamina Lubricants",
    "PT Holcim Indonesia",
    "PT Krakatau Steel",
    "PT Charoen Pokphand Indonesia",
    "PT Mayora Indah",
    "PT Garudafood Putra Putri Jaya",
    "PT Wings Food",
    "PT Nestle Indonesia",
    "PT Frisian Flag Indonesia",
    "PT Beiersdorf Indonesia",
    "PT Procter Gamble Home Products Indonesia",
    "PT Reckitt Benckiser Indonesia",
    "PT 3M Indonesia",
    "PT Siemens Indonesia",
    "PT ABB Sakti Industri",
    "PT Schneider Electric Manufacturing",
    "PT Philips Industries Batam",
    "PT Epson Indonesia",
    "PT Fuji Xerox Indonesia",
]

# ── Foreign exporters ──────────────────────────────────────────────────────────
EXPORTERS = [
    # Korea
    "Samsung Electronics Co., Ltd",
    "LG Electronics Inc.",
    "Hyundai Motor Company",
    "Kia Corporation",
    "SK Hynix Inc.",
    "Posco Co., Ltd",
    "LG Chem Ltd",
    "Hanwha Solutions Corporation",
    # China
    "Foxconn Industrial Internet Co., Ltd",
    "Haier Group Corporation",
    "Midea Group Co., Ltd",
    "BYD Auto Co., Ltd",
    "SAIC Motor Corporation",
    "Huawei Technologies Co., Ltd",
    "Lenovo Group Limited",
    "Xiaomi Corporation",
    "CNOOC Limited",
    "Sinopec Corp",
    "Zhejiang Geely Holding Group",
    "BOE Technology Group Co., Ltd",
    # Japan
    "Toyota Motor Corporation",
    "Honda Motor Co., Ltd",
    "Mitsubishi Electric Corporation",
    "Panasonic Holdings Corporation",
    "Sony Group Corporation",
    "Canon Inc.",
    "Nikon Corporation",
    "Bridgestone Corporation",
    "Sumitomo Chemical Co., Ltd",
    "Toray Industries Inc.",
    # USA
    "Apple Inc.",
    "3M Company",
    "Exxon Mobil Corporation",
    "Procter & Gamble Company",
    "Caterpillar Inc.",
    "Cargill Incorporated",
    "Archer Daniels Midland Company",
    # Germany
    "BASF SE",
    "Siemens AG",
    "Bosch GmbH",
    "BMW AG",
    "Bayer AG",
    # Netherlands
    "Royal Dutch Shell plc",
    "Philips N.V.",
    "Unilever N.V.",
]

# ── HS codes with metadata ─────────────────────────────────────────────────────
HS_CODES = [
    # Electronics — moderate risk
    {"code": "8471.30.00", "desc": "Laptops / portable computers",         "category": "Electronics",  "base_value": (800, 5000),   "restricted": False, "risk_adj": 10},
    {"code": "8517.12.00", "desc": "Smartphones and mobile phones",        "category": "Electronics",  "base_value": (200, 800),    "restricted": False, "risk_adj": 10},
    {"code": "8528.72.00", "desc": "LCD / LED televisions",                "category": "Electronics",  "base_value": (150, 1200),   "restricted": False, "risk_adj": 8},
    {"code": "8542.31.00", "desc": "Integrated circuits / processors",     "category": "Electronics",  "base_value": (500, 15000),  "restricted": False, "risk_adj": 12},
    {"code": "8443.31.00", "desc": "Printing machines",                    "category": "Electronics",  "base_value": (300, 3000),   "restricted": False, "risk_adj": 5},
    {"code": "8504.40.00", "desc": "Static converters / power supply",     "category": "Electronics",  "base_value": (200, 2500),   "restricted": False, "risk_adj": 5},
    # Auto parts — low risk
    {"code": "8708.29.00", "desc": "Body parts for motor vehicles",        "category": "Auto Parts",   "base_value": (1000, 30000), "restricted": False, "risk_adj": 3},
    {"code": "8708.99.00", "desc": "Other parts for motor vehicles",       "category": "Auto Parts",   "base_value": (500, 20000),  "restricted": False, "risk_adj": 3},
    {"code": "4011.10.00", "desc": "Pneumatic tyres for motor cars",       "category": "Auto Parts",   "base_value": (2000, 25000), "restricted": False, "risk_adj": 3},
    {"code": "8407.34.00", "desc": "Reciprocating piston engines",         "category": "Machinery",    "base_value": (5000, 80000), "restricted": False, "risk_adj": 5},
    # Chemicals — high risk (some restricted)
    {"code": "2710.19.00", "desc": "Petroleum oils and preparations",      "category": "Chemicals",    "base_value": (10000, 150000),"restricted": True,  "risk_adj": 30},
    {"code": "2711.21.00", "desc": "Natural gas in gaseous state",         "category": "Chemicals",    "base_value": (20000, 200000),"restricted": True,  "risk_adj": 30},
    {"code": "3901.10.00", "desc": "Polyethylene with density < 0.94",     "category": "Chemicals",    "base_value": (3000, 40000), "restricted": False, "risk_adj": 8},
    {"code": "2902.20.00", "desc": "Benzene",                              "category": "Chemicals",    "base_value": (5000, 60000), "restricted": True,  "risk_adj": 25},
    {"code": "3004.90.00", "desc": "Pharmaceutical preparations",          "category": "Pharma",       "base_value": (5000, 80000), "restricted": False, "risk_adj": 10},
    # Textiles — low risk
    {"code": "6110.20.00", "desc": "Jerseys, pullovers of cotton",         "category": "Textiles",     "base_value": (500, 8000),   "restricted": False, "risk_adj": 2},
    {"code": "6203.42.00", "desc": "Mens trousers of cotton",              "category": "Textiles",     "base_value": (300, 5000),   "restricted": False, "risk_adj": 2},
    {"code": "6204.62.00", "desc": "Womens trousers of cotton",            "category": "Textiles",     "base_value": (300, 5000),   "restricted": False, "risk_adj": 2},
    {"code": "5208.21.00", "desc": "Woven fabrics of cotton",              "category": "Textiles",     "base_value": (1000, 15000), "restricted": False, "risk_adj": 2},
    # Food & Beverage — low risk
    {"code": "0901.11.00", "desc": "Coffee, not roasted, not decaffeinated","category": "Food",        "base_value": (2000, 20000), "restricted": False, "risk_adj": 2},
    {"code": "1006.30.00", "desc": "Semi-milled or wholly milled rice",    "category": "Food",         "base_value": (1000, 30000), "restricted": False, "risk_adj": 3},
    {"code": "2106.90.00", "desc": "Food preparations NES",                "category": "Food",         "base_value": (500, 10000),  "restricted": False, "risk_adj": 3},
    {"code": "2009.89.00", "desc": "Juice of other single fruit",          "category": "Food",         "base_value": (500, 8000),   "restricted": False, "risk_adj": 2},
    # Steel & Materials — moderate risk
    {"code": "7208.51.00", "desc": "Flat-rolled products of iron / steel", "category": "Metals",       "base_value": (5000, 80000), "restricted": False, "risk_adj": 8},
    {"code": "7606.12.00", "desc": "Rectangular aluminium plates",         "category": "Metals",       "base_value": (3000, 40000), "restricted": False, "risk_adj": 6},
    # Weapons — very high risk (restricted)
    {"code": "9301.00.00", "desc": "Military weapons",                     "category": "Weapons",      "base_value": (10000, 500000),"restricted": True,  "risk_adj": 50},
    {"code": "9302.00.00", "desc": "Revolvers and pistols",                "category": "Weapons",      "base_value": (5000, 100000),"restricted": True,  "risk_adj": 50},
    # Machinery — low-moderate risk
    {"code": "8457.10.00", "desc": "Machining centres for working metal",  "category": "Machinery",    "base_value": (20000, 300000),"restricted": False, "risk_adj": 5},
    {"code": "8421.21.00", "desc": "Water filtration / purifying machinery","category": "Machinery",   "base_value": (3000, 50000), "restricted": False, "risk_adj": 4},
    {"code": "8477.10.00", "desc": "Injection moulding machines",          "category": "Machinery",    "base_value": (10000, 150000),"restricted": False, "risk_adj": 5},
    # Consumer goods
    {"code": "9401.61.00", "desc": "Seats with wooden frames",             "category": "Furniture",    "base_value": (500, 10000),  "restricted": False, "risk_adj": 2},
    {"code": "9403.20.00", "desc": "Metal furniture",                      "category": "Furniture",    "base_value": (1000, 20000), "restricted": False, "risk_adj": 2},
    {"code": "3401.11.00", "desc": "Soap for toilet use",                  "category": "FMCG",         "base_value": (500, 8000),   "restricted": False, "risk_adj": 2},
]

# ── Shipping ───────────────────────────────────────────────────────────────────
SHIPPING_LINES = ["TCKU", "MSCU", "MAEU", "HLCU", "CMAU", "OOLU", "EVGR", "YMLU", "APHU", "KKFU"]

VESSELS = [
    "MV Maersk Seletar", "MV MSC Gaia", "MV CMA CGM Coral", "MV Evergreen Universe",
    "MV Yang Ming Wellness", "MV Hapag Jakarta Express", "MV OOCL Indonesia",
    "MV Pacific Star", "MV Asian Spirit", "MV Nusantara Express",
    "MV Jaya Kencana", "MV Sinar Bandung", "MV Bunga Teratai",
    "MV APL Singapore", "MV Cosco Harmony", "MV Wan Hai 232",
    "MV Mataram Star", "MV Meratus Palembang", "MV Tanto Aman",
    "MV Dharma Kencana VIII", "MV Karunia Sejahtera", "MV Selat Malaka",
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

DOC_TYPES = ["commercial_invoice", "bill_of_lading", "packing_list"]
CONFIDENCE = ["high", "high", "high", "medium", "low"]  # weighted toward high


def _container_id():
    prefix = random.choice(SHIPPING_LINES)
    digits = "".join([str(random.randint(0, 9)) for _ in range(7)])
    return f"{prefix}{digits}"


def _invoice_number():
    year = random.choice([2025, 2026])
    num = random.randint(1, 9999)
    prefix = random.choice(["INV", "SI", "PO", "CI", "SO"])
    return f"{prefix}-{year}-{num:04d}"


def _weight_pair(cartons, category):
    base = random.uniform(5, 50) * cartons
    net = round(base * random.uniform(0.8, 0.95), 2)
    gross = round(base, 2)
    return net, gross


def _invoice_value(hs_meta, cartons, quantity_per_carton=10):
    lo, hi = hs_meta["base_value"]
    unit_price = random.uniform(lo / (cartons * quantity_per_carton), hi / (cartons * quantity_per_carton))
    total = round(unit_price * cartons * quantity_per_carton, 2)
    return total


def _label_jalur(record: dict) -> str:
    """Deterministic labelling logic that mirrors real CEISA patterns."""
    risk = 0

    # Missing critical fields
    if not record["hs_code"]:         risk += 25
    if not record["importer"]:        risk += 20
    if not record["container_id"]:    risk += 20
    if not record["invoice_value"]:   risk += 15
    if not record["exporter"]:        risk += 10
    if not record["vessel_name"]:     risk += 5
    if not record["port_of_origin"]:  risk += 5

    # Restricted HS code
    if record.get("hs_restricted"):   risk += record.get("hs_risk_adj", 0)

    # OCR confidence
    conf_map = {"high": 0, "medium": 5, "low": 20}
    risk += conf_map.get(record["confidence_badge"], 5)

    # Very high value without container
    try:
        val = float(str(record["invoice_value_usd"]).replace(",", ""))
        if val > 100_000 and not record["container_id"]:
            risk += 20
        if val > 500_000:
            risk += 10
    except (ValueError, TypeError):
        pass

    # Apply HS risk adjustment for non-restricted
    risk += record.get("hs_risk_adj", 0) // 3

    # Noise (real data isn't perfectly deterministic)
    risk += random.randint(-5, 8)
    risk = max(0, min(100, risk))

    if risk < 30:   return "green"
    if risk < 70:   return "yellow"
    return "red"


def _make_record(doc_type: str, profile: str) -> dict:
    """
    profile: "clean" | "partial" | "risky" | "missing"
    """
    hs_meta = random.choice(HS_CODES)

    # For risky profile, prefer restricted or high-adj codes
    if profile == "risky":
        candidates = [h for h in HS_CODES if h["restricted"] or h["risk_adj"] >= 20]
        hs_meta = random.choice(candidates) if candidates else hs_meta

    importer = random.choice(IMPORTERS)
    exporter = random.choice(EXPORTERS)
    cartons = random.randint(1, 500)
    invoice_usd = round(_invoice_value(hs_meta, cartons), 2)
    net_kg, gross_kg = _weight_pair(cartons, hs_meta["category"])
    vessel = random.choice(VESSELS)
    port = random.choice(PORTS)
    confidence = random.choices(CONFIDENCE, k=1)[0]
    if profile == "risky":
        confidence = random.choice(["low", "medium"])

    # Base record — all fields present
    rec = {
        "scan_id": str(uuid.uuid4()),
        "document_type": doc_type,
        "hs_code": hs_meta["code"],
        "hs_description": hs_meta["desc"],
        "hs_category": hs_meta["category"],
        "hs_restricted": hs_meta["restricted"],
        "hs_risk_adj": hs_meta["risk_adj"],
        "invoice_value": f"USD {invoice_usd:,.2f}",
        "invoice_value_usd": invoice_usd,
        "invoice_number": _invoice_number(),
        "container_id": _container_id(),
        "importer": importer,
        "exporter": exporter,
        "net_weight": f"{net_kg} KG",
        "gross_weight": f"{gross_kg} KG",
        "vessel_name": vessel,
        "port_of_origin": port,
        "carton_count": str(cartons),
        "confidence_badge": confidence,
        "scanned_at": (datetime(2026, 1, 1) + timedelta(
            days=random.randint(0, 171),
            hours=random.randint(6, 22),
            minutes=random.randint(0, 59),
        )).isoformat(),
        "operator_id": random.choice(["CDP-001", "CDP-002", "CDP-003"]),
    }

    # Apply missing-field patterns per profile
    if profile == "partial":
        # Randomly blank 1–3 non-critical fields
        optional = ["exporter", "vessel_name", "port_of_origin", "carton_count", "invoice_number"]
        for field in random.sample(optional, k=random.randint(1, 2)):
            rec[field] = ""

    elif profile == "missing":
        # Blank 2–4 critical fields
        critical = ["hs_code", "invoice_value", "container_id", "importer", "exporter"]
        for field in random.sample(critical, k=random.randint(2, 4)):
            rec[field] = ""
        rec["invoice_value_usd"] = 0

    elif profile == "risky":
        # May have some fields missing + high value
        if random.random() < 0.4:
            rec["container_id"] = ""
        if random.random() < 0.3:
            rec["exporter"] = ""
        # Inflate invoice value for some risky records
        if random.random() < 0.5:
            rec["invoice_value_usd"] = invoice_usd * random.uniform(5, 20)
            rec["invoice_value"] = f"USD {rec['invoice_value_usd']:,.2f}"

    # Compute label
    rec["jalur"] = _label_jalur(rec)

    # Numeric label for XGBoost
    rec["jalur_label"] = {"green": 0, "yellow": 1, "red": 2}[rec["jalur"]]

    # Missing field count (feature)
    critical_fields = ["hs_code", "invoice_value", "container_id", "importer", "exporter",
                       "vessel_name", "port_of_origin"]
    rec["missing_field_count"] = sum(1 for f in critical_fields if not rec.get(f))

    return rec


def generate(n: int = 600) -> list[dict]:
    records = []

    # Distribution: clean 55%, partial 25%, missing 12%, risky 8%
    for doc_type in DOC_TYPES:
        per_type = n // len(DOC_TYPES)
        counts = {
            "clean":   int(per_type * 0.55),
            "partial": int(per_type * 0.25),
            "missing": int(per_type * 0.12),
            "risky":   per_type - int(per_type * 0.55) - int(per_type * 0.25) - int(per_type * 0.12),
        }
        for profile, count in counts.items():
            for _ in range(count):
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
    out = Path(__file__).parent.parent / "data" / "training_declarations.csv"
    out.parent.mkdir(exist_ok=True)

    records = generate(600)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    # Summary
    from collections import Counter
    jalur_dist = Counter(r["jalur"] for r in records)
    doc_dist   = Counter(r["document_type"] for r in records)
    print(f"Generated {len(records)} records → {out}")
    print(f"Jalur distribution: {dict(jalur_dist)}")
    print(f"Doc type distribution: {dict(doc_dist)}")
    print(f"Sample records:")
    for r in records[:3]:
        print(f"  [{r['jalur'].upper():6}] {r['document_type']:20} HS={r['hs_code']} "
              f"val={r['invoice_value'][:12]} importer={r['importer'][:30]}")
