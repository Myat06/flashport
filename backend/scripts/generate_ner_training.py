"""
Generate spaCy NER training data for customs document field extraction.

Produces ~300 annotated text examples covering all three document types.
Each example is a realistic text snippet (like Tesseract OCR output)
with entity spans labelled for each customs field.

Output: data/ner_training.spacy
Usage:  python scripts/generate_ner_training.py
"""
import random
from pathlib import Path

import spacy
from spacy.tokens import DocBin

random.seed(42)

# ── Entity labels ─────────────────────────────────────────────────────────────
LABELS = [
    "HS_CODE", "INVOICE_VALUE", "CONTAINER_ID", "IMPORTER", "EXPORTER",
    "NET_WEIGHT", "GROSS_WEIGHT", "VESSEL_NAME", "PORT_OF_ORIGIN",
    "INVOICE_NUMBER", "CARTON_COUNT",
]

# ── Data pools ────────────────────────────────────────────────────────────────
HS_CODES = [
    "8471.30.00", "8517.12.00", "8528.72.00", "8542.31.00", "8708.29.00",
    "4011.10.00", "6110.20.00", "3004.90.00", "8443.31.00", "3901.10.00",
    "0901.11.00", "7208.51.00", "9401.61.00", "6203.42.00", "8504.40.00",
    "2710.19.00", "9301.00.00", "8457.10.00", "8421.21.00", "2902.20.00",
]

IMPORTERS = [
    "PT Astra Honda Motor", "PT Toyota Motor Manufacturing Indonesia",
    "PT Unilever Indonesia Tbk", "PT Kalbe Farma Tbk",
    "PT Samsung Electronics Indonesia", "PT Sharp Electronics Indonesia",
    "PT LG Electronics Indonesia", "PT Panasonic Manufacturing Indonesia",
    "PT Indofood Sukses Makmur Tbk", "PT Cikarang Listrindo Tbk",
    "PT Maju Jaya Abadi", "PT Sinar Harapan Nusantara",
    "PT Jababeka Infrastruktur", "PT Multi Bintang Indonesia",
    "PT Charoen Pokphand Indonesia", "PT Mayora Indah Tbk",
    "PT Garudafood Putra Putri Jaya", "PT Wings Food",
    "PT Holcim Indonesia", "PT Krakatau Steel Tbk",
]

EXPORTERS = [
    "Samsung Electronics Co., Ltd", "LG Electronics Inc.",
    "Toyota Motor Corporation", "Foxconn Industrial Internet Co., Ltd",
    "Haier Group Corporation", "Mitsubishi Electric Corporation",
    "Apple Inc.", "BASF SE", "Siemens AG", "Midea Group Co., Ltd",
    "Posco Co., Ltd", "Bridgestone Corporation",
    "Canon Inc.", "Sony Group Corporation", "Panasonic Holdings Corporation",
    "Hyundai Motor Company", "BYD Auto Co., Ltd", "Lenovo Group Limited",
    "3M Company", "Procter and Gamble Company",
]

VESSELS = [
    "MV Maersk Seletar", "MV MSC Gaia", "MV CMA CGM Coral",
    "MV Evergreen Universe", "MV Yang Ming Wellness",
    "MV Hapag Jakarta Express", "MV OOCL Indonesia",
    "MV Pacific Star", "MV Cosco Harmony", "MV Wan Hai 232",
    "MV Nusantara Express", "MV Jaya Kencana", "MV Sinar Bandung",
    "MV APL Singapore", "MV Mataram Star",
]

PORTS = [
    "Busan, Korea", "Shanghai, China", "Guangzhou, China",
    "Shenzhen, China", "Tianjin, China", "Qingdao, China",
    "Yokohama, Japan", "Osaka, Japan", "Rotterdam, Netherlands",
    "Singapore", "Port Klang, Malaysia", "Ho Chi Minh City, Vietnam",
    "Hamburg, Germany", "Los Angeles, USA", "Ningbo, China",
]

INV_PREFIXES   = ["INV", "SI", "CI", "PO", "SO"]
SHIP_PREFIXES  = ["TCKU", "MSCU", "MAEU", "HLCU", "CMAU", "OOLU", "EVGR", "YMLU", "APHU"]

# ── Helpers ───────────────────────────────────────────────────────────────────
def _hs():  return random.choice(HS_CODES)
def _imp(): return random.choice(IMPORTERS)
def _exp(): return random.choice(EXPORTERS)
def _ves(): return random.choice(VESSELS)
def _port(): return random.choice(PORTS)
def _inv_no(): return f"{random.choice(INV_PREFIXES)}-2026-{random.randint(1000,9999)}"
def _cont(): return f"{random.choice(SHIP_PREFIXES)}{''.join(str(random.randint(0,9)) for _ in range(7))}"
def _usd(): return f"USD {random.randint(500,500_000):,}.{random.randint(0,99):02d}"
def _kg(lo=50, hi=5000): return f"{round(random.uniform(lo,hi), 2)} KG"
def _ctns(): return str(random.randint(1, 500))

def _find(text: str, value: str):
    """Return (start, end) of value in text, or None."""
    i = text.find(value)
    return (i, i + len(value)) if i >= 0 else None

def _ann(text: str, spans: list[tuple]) -> dict | None:
    """Build spaCy annotation dict, skip if any span not found."""
    entities = []
    for value, label in spans:
        pos = _find(text, value)
        if pos is None:
            return None
        entities.append((pos[0], pos[1], label))
    # Check no overlaps
    for i, (s1, e1, _) in enumerate(entities):
        for s2, e2, _ in entities[i+1:]:
            if s1 < e2 and s2 < e1:
                return None
    return {"entities": entities}

# ── Text templates ────────────────────────────────────────────────────────────

def gen_commercial_invoice():
    hs, imp, exp, ves, port = _hs(), _imp(), _exp(), _ves(), _port()
    inv_no, cont, usd = _inv_no(), _cont(), _usd()
    net, gross, ctns = _kg(100, 3000), _kg(110, 3200), _ctns()

    templates = [
        (
            f"COMMERCIAL INVOICE\n"
            f"Invoice No.: {inv_no}   Date: 22 June 2026\n"
            f"SHIPPER / EXPORTER: {exp}\n"
            f"CONSIGNEE / IMPORTER: {imp}\n"
            f"PORT OF LOADING: {port}\n"
            f"PORT OF DISCHARGE: Cikarang Dry Port, Bekasi, Indonesia\n"
            f"VESSEL: {ves}\n"
            f"CONTAINER NO.: {cont}\n"
            f"HS Code: {hs}\n"
            f"Total Value: {usd}\n"
            f"Net Weight: {net}   Gross Weight: {gross}\n"
            f"Total Cartons: {ctns} CTN",
            [(inv_no,"INVOICE_NUMBER"),(exp,"EXPORTER"),(imp,"IMPORTER"),
             (port,"PORT_OF_ORIGIN"),(ves,"VESSEL_NAME"),(cont,"CONTAINER_ID"),
             (hs,"HS_CODE"),(usd,"INVOICE_VALUE"),(net,"NET_WEIGHT"),
             (gross,"GROSS_WEIGHT"),(ctns,"CARTON_COUNT")]
        ),
        (
            f"FAKTUR KOMERSIAL / COMMERCIAL INVOICE\n"
            f"No. Faktur: {inv_no}\n"
            f"Pengirim / Shipper: {exp}\n"
            f"Penerima / Consignee: {imp}\n"
            f"Pelabuhan Muat / Port of Loading: {port}\n"
            f"Pelabuhan Bongkar: Cikarang Dry Port\n"
            f"Nama Kapal / Vessel Name: {ves}\n"
            f"No. Kontainer / Container No.: {cont}\n"
            f"Pos Tarif / HS Code: {hs}\n"
            f"Nilai Faktur / Invoice Value: {usd}\n"
            f"Berat Bersih / Net Weight: {net}\n"
            f"Berat Kotor / Gross Weight: {gross}\n"
            f"Jumlah Koli: {ctns} Karton",
            [(inv_no,"INVOICE_NUMBER"),(exp,"EXPORTER"),(imp,"IMPORTER"),
             (port,"PORT_OF_ORIGIN"),(ves,"VESSEL_NAME"),(cont,"CONTAINER_ID"),
             (hs,"HS_CODE"),(usd,"INVOICE_VALUE"),(net,"NET_WEIGHT"),
             (gross,"GROSS_WEIGHT"),(ctns,"CARTON_COUNT")]
        ),
        (
            f"Invoice Number: {inv_no}\n"
            f"From: {exp}\n"
            f"To: {imp}\n"
            f"Vessel: {ves}  Container: {cont}\n"
            f"Loading Port: {port}\n"
            f"HS: {hs}  Amount: {usd}\n"
            f"N.W.: {net}  G.W.: {gross}  Cartons: {ctns}",
            [(inv_no,"INVOICE_NUMBER"),(exp,"EXPORTER"),(imp,"IMPORTER"),
             (ves,"VESSEL_NAME"),(cont,"CONTAINER_ID"),(port,"PORT_OF_ORIGIN"),
             (hs,"HS_CODE"),(usd,"INVOICE_VALUE"),(net,"NET_WEIGHT"),
             (gross,"GROSS_WEIGHT"),(ctns,"CARTON_COUNT")]
        ),
    ]
    return random.choice(templates)


def gen_bill_of_lading():
    hs, imp, exp, ves, port = _hs(), _imp(), _exp(), _ves(), _port()
    bl_no, cont = _inv_no().replace("INV","BL"), _cont()
    gross, ctns = _kg(200, 8000), _ctns()

    templates = [
        (
            f"BILL OF LADING\n"
            f"B/L No.: {bl_no}\n"
            f"Shipper: {exp}\n"
            f"Consignee: {imp}\n"
            f"Notify Party: {imp}\n"
            f"Port of Loading: {port}\n"
            f"Port of Discharge: Tanjung Priok, Jakarta, Indonesia\n"
            f"Place of Delivery: Cikarang Dry Port, Bekasi\n"
            f"Vessel: {ves}\n"
            f"Container No.: {cont}\n"
            f"HS Code: {hs}\n"
            f"No. of Packages: {ctns} Cartons\n"
            f"Gross Weight: {gross}",
            [(bl_no,"INVOICE_NUMBER"),(exp,"EXPORTER"),(imp,"IMPORTER"),
             (port,"PORT_OF_ORIGIN"),(ves,"VESSEL_NAME"),(cont,"CONTAINER_ID"),
             (hs,"HS_CODE"),(ctns,"CARTON_COUNT"),(gross,"GROSS_WEIGHT")]
        ),
        (
            f"KONOSEMEN / BILL OF LADING  No. {bl_no}\n"
            f"Pengirim: {exp}\n"
            f"Penerima: {imp}\n"
            f"Pelabuhan Muat: {port}\n"
            f"Pelabuhan Tujuan: Tanjung Priok Jakarta\n"
            f"Tempat Penyerahan: Cikarang Dry Port\n"
            f"Kapal: {ves}   Kontainer: {cont}\n"
            f"Pos Tarif HS: {hs}\n"
            f"Jumlah Karton: {ctns}\n"
            f"Berat Kotor: {gross}",
            [(bl_no,"INVOICE_NUMBER"),(exp,"EXPORTER"),(imp,"IMPORTER"),
             (port,"PORT_OF_ORIGIN"),(ves,"VESSEL_NAME"),(cont,"CONTAINER_ID"),
             (hs,"HS_CODE"),(ctns,"CARTON_COUNT"),(gross,"GROSS_WEIGHT")]
        ),
    ]
    return random.choice(templates)


def gen_packing_list():
    hs, imp, exp, ves, port = _hs(), _imp(), _exp(), _ves(), _port()
    pl_no, cont = _inv_no().replace("INV","PL"), _cont()
    net, gross, ctns = _kg(80, 4000), _kg(90, 4200), _ctns()

    templates = [
        (
            f"PACKING LIST / DAFTAR KEMASAN\n"
            f"Packing List No.: {pl_no}\n"
            f"Exporter: {exp}\n"
            f"Importer: {imp}\n"
            f"Vessel: {ves}   Container: {cont}\n"
            f"Port of Loading: {port}\n"
            f"Port of Discharge: Cikarang Dry Port, Bekasi, Indonesia\n"
            f"HS Code: {hs}\n"
            f"Total Cartons: {ctns}\n"
            f"Total Net Weight: {net}\n"
            f"Total Gross Weight: {gross}",
            [(pl_no,"INVOICE_NUMBER"),(exp,"EXPORTER"),(imp,"IMPORTER"),
             (ves,"VESSEL_NAME"),(cont,"CONTAINER_ID"),(port,"PORT_OF_ORIGIN"),
             (hs,"HS_CODE"),(ctns,"CARTON_COUNT"),(net,"NET_WEIGHT"),(gross,"GROSS_WEIGHT")]
        ),
        (
            f"PL No. {pl_no}\n"
            f"Pengirim / From: {exp}\n"
            f"Penerima / To: {imp}\n"
            f"Kapal: {ves}   No. Kontainer: {cont}\n"
            f"Pelabuhan Asal: {port}\n"
            f"Pos Tarif: {hs}\n"
            f"Jumlah Koli: {ctns} CTN\n"
            f"Berat Bersih: {net}\n"
            f"Berat Kotor: {gross}",
            [(pl_no,"INVOICE_NUMBER"),(exp,"EXPORTER"),(imp,"IMPORTER"),
             (ves,"VESSEL_NAME"),(cont,"CONTAINER_ID"),(port,"PORT_OF_ORIGIN"),
             (hs,"HS_CODE"),(ctns,"CARTON_COUNT"),(net,"NET_WEIGHT"),(gross,"GROSS_WEIGHT")]
        ),
    ]
    return random.choice(templates)


# ── Partial / noisy examples ──────────────────────────────────────────────────

def gen_partial():
    """Missing some fields — teaches NER to extract only what's present."""
    hs, imp, cont = _hs(), _imp(), _cont()
    usd = _usd()
    text = (
        f"CUSTOMS DECLARATION\n"
        f"Consignee: {imp}\n"
        f"HS Tariff Code: {hs}\n"
        f"Declared Value: {usd}\n"
        f"Container: {cont}\n"
        f"Port of Origin: Not specified\n"
        f"Vessel: Unknown"
    )
    spans = [(imp,"IMPORTER"),(hs,"HS_CODE"),(usd,"INVOICE_VALUE"),(cont,"CONTAINER_ID")]
    return text, spans


def gen_single_field():
    """Single-field snippets — important for NER robustness."""
    options = [
        (f"HS Code: {_hs()}", [(_hs(), "HS_CODE")]),
        (f"Pos. Tarif: {_hs()}", [(_hs(), "HS_CODE")]),
        (f"Container No.: {_cont()}", [(_cont(), "CONTAINER_ID")]),
        (f"Kontainer: {_cont()}", [(_cont(), "CONTAINER_ID")]),
        (f"Total Value: {_usd()}", [(_usd(), "INVOICE_VALUE")]),
        (f"Nilai: {_usd()}", [(_usd(), "INVOICE_VALUE")]),
        (f"Net Weight: {_kg()}", [(_kg(), "NET_WEIGHT")]),
        (f"Berat Bersih: {_kg()}", [(_kg(), "NET_WEIGHT")]),
        (f"Gross Weight: {_kg()}", [(_kg(), "GROSS_WEIGHT")]),
        (f"Berat Kotor: {_kg()}", [(_kg(), "GROSS_WEIGHT")]),
        (f"Vessel: {_ves()}", [(_ves(), "VESSEL_NAME")]),
        (f"Kapal: {_ves()}", [(_ves(), "VESSEL_NAME")]),
        (f"Consignee: {_imp()}", [(_imp(), "IMPORTER")]),
        (f"Penerima: {_imp()}", [(_imp(), "IMPORTER")]),
        (f"Shipper: {_exp()}", [(_exp(), "EXPORTER")]),
        (f"Pengirim: {_exp()}", [(_exp(), "EXPORTER")]),
        (f"Port of Loading: {_port()}", [(_port(), "PORT_OF_ORIGIN")]),
        (f"Pelabuhan Asal: {_port()}", [(_port(), "PORT_OF_ORIGIN")]),
        (f"Invoice No.: {_inv_no()}", [(_inv_no(), "INVOICE_NUMBER")]),
        (f"No. Faktur: {_inv_no()}", [(_inv_no(), "INVOICE_NUMBER")]),
        (f"Cartons: {_ctns()} CTN", [(_ctns(), "CARTON_COUNT")]),
        (f"Jumlah Koli: {_ctns()}", [(_ctns(), "CARTON_COUNT")]),
    ]
    return random.choice(options)


# ── Build dataset ─────────────────────────────────────────────────────────────

def build_dataset(n: int = 300) -> list[tuple]:
    """Return list of (text, annotation) pairs."""
    examples = []
    generators = [
        (gen_commercial_invoice, 80),
        (gen_bill_of_lading,     70),
        (gen_packing_list,       70),
        (gen_partial,            40),
        (gen_single_field,       40),
    ]
    for gen_fn, count in generators:
        attempts = 0
        while len([e for e in examples if e[0].startswith(gen_fn.__name__[:3])]) < count:
            text, spans = gen_fn()
            ann = _ann(text, spans)
            if ann:
                examples.append((text, ann))
            attempts += 1
            if attempts > count * 10:
                break

    # Fill remainder
    while len(examples) < n:
        gen_fn = random.choice([gen_commercial_invoice, gen_bill_of_lading, gen_packing_list])
        text, spans = gen_fn()
        ann = _ann(text, spans)
        if ann:
            examples.append((text, ann))

    random.shuffle(examples)
    return examples[:n]


def main():
    out = Path(__file__).parent.parent / "data" / "ner_training.spacy"
    out.parent.mkdir(exist_ok=True)

    nlp = spacy.blank("en")
    db = DocBin()

    examples = []
    # Generate enough raw examples
    attempts = 0
    while len(examples) < 300 and attempts < 5000:
        attempts += 1
        gen_fn = random.choice([
            gen_commercial_invoice, gen_bill_of_lading,
            gen_packing_list, gen_partial, gen_single_field,
        ])
        text, spans = gen_fn()
        ann = _ann(text, spans)
        if ann and ann["entities"]:
            examples.append((text, ann))

    print(f"Generated {len(examples)} valid training examples")

    for text, ann in examples:
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in ann["entities"]:
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span:
                ents.append(span)
        doc.ents = ents
        db.add(doc)

    db.to_disk(str(out))
    print(f"Saved to {out}")

    # Entity distribution
    from collections import Counter
    label_counts = Counter()
    for _, ann in examples:
        for _, _, label in ann["entities"]:
            label_counts[label] += 1
    print("\nEntity distribution:")
    for label, count in sorted(label_counts.items()):
        print(f"  {label:20} {count}")


if __name__ == "__main__":
    main()
