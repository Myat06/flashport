"""
Sample customs document generator for FlashPort training data.

Generates realistic Indonesian customs documents:
  - Commercial Invoice (Faktur Komersial)
  - Bill of Lading (Konosemen / B/L)
  - Packing List (Daftar Kemasan)

Output: backend/data/sample_docs/
  ├── commercial_invoice/   (PDF + JPG)
  ├── bill_of_lading/       (PDF + JPG)
  └── packing_list/         (PDF + JPG)

Usage:
    cd backend
    source venv/bin/activate
    python scripts/generate_sample_docs.py
"""
import io
import random
from datetime import datetime, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

random.seed(0)

# ── Output directory ──────────────────────────────────────────────────────────
BASE_OUT = Path(__file__).parent.parent / "data" / "sample_docs"
DIRS = {
    "commercial_invoice": BASE_OUT / "commercial_invoice",
    "bill_of_lading":     BASE_OUT / "bill_of_lading",
    "packing_list":       BASE_OUT / "packing_list",
}

# ── Sample data pools ─────────────────────────────────────────────────────────
IMPORTERS = [
    ("PT Astra Honda Motor",              "Jl. Raya Pegangsaan Dua KM 2.2, Kelapa Gading, Jakarta Utara 14250, Indonesia"),
    ("PT Toyota Motor Manufacturing Indonesia", "Jl. Yos Sudarso, Sunter II, Jakarta Utara 14350, Indonesia"),
    ("PT Unilever Indonesia Tbk",         "Jl. BSD Boulevard Barat, BSD City, Tangerang 15322, Indonesia"),
    ("PT Kalbe Farma Tbk",                "Jl. Let. Jend. Suprapto Kav. 4, Cempaka Putih, Jakarta Pusat 10510, Indonesia"),
    ("PT Samsung Electronics Indonesia",  "Jl. Jababeka Raya Blok F29-33, Cikarang, Bekasi 17530, Indonesia"),
    ("PT Sharp Electronics Indonesia",    "Jl. Swadaya IV, Rawaterate, Cakung, Jakarta Timur 13920, Indonesia"),
    ("PT LG Electronics Indonesia",       "Jl. Jend. Gatot Subroto Kav. 9-11, Menara Mulia Lt. 15, Jakarta 12930, Indonesia"),
    ("PT Panasonic Manufacturing Indonesia", "Jl. Raya Bogor KM 29, Pekayon, Pasar Rebo, Jakarta Timur 13710, Indonesia"),
    ("PT Indofood Sukses Makmur Tbk",     "Sudirman Plaza, Indofood Tower Lantai 21, Jl. Jend. Sudirman Kav. 76-78, Jakarta 12910, Indonesia"),
    ("PT Cikarang Listrindo Tbk",         "Jl. Jababeka XVI, Kawasan Industri Jababeka, Cikarang, Bekasi 17530, Indonesia"),
]

EXPORTERS = [
    ("Samsung Electronics Co., Ltd",      "129, Samsung-ro, Yeongtong-gu, Suwon-si, Gyeonggi-do 16677, Republic of Korea"),
    ("LG Electronics Inc.",               "LG Twin Towers, 128 Yeoui-daero, Yeongdeungpo-gu, Seoul 07336, Republic of Korea"),
    ("Toyota Motor Corporation",          "1 Toyota-cho, Toyota, Aichi 471-8571, Japan"),
    ("Foxconn Industrial Internet Co.",   "2 Torch Rd, Zhengzhou Economic Development Zone, Henan 450016, China"),
    ("Haier Group Corporation",           "No. 1 Haier Road, Qingdao, Shandong 266101, China"),
    ("Mitsubishi Electric Corporation",   "2-7-3 Marunouchi, Chiyoda-ku, Tokyo 100-8310, Japan"),
    ("Apple Inc.",                        "One Apple Park Way, Cupertino, California 95014, United States"),
    ("BASF SE",                           "Carl-Bosch-Str. 38, 67056 Ludwigshafen am Rhein, Germany"),
    ("Siemens AG",                        "Werner-von-Siemens-Str. 1, 80333 München, Germany"),
    ("Midea Group Co., Ltd",              "6 Midea Avenue, Shunde, Foshan, Guangdong 528311, China"),
    ("Posco Co., Ltd",                    "440 Cheongam-ro, Nam-gu, Pohang-si, Gyeongbuk 37859, Republic of Korea"),
    ("Bridgestone Corporation",           "3-1-1 Kyobashi, Chuo-ku, Tokyo 104-8340, Japan"),
]

GOODS = [
    {"hs":  "8471.30.00", "desc": "Portable Automatic Data Processing Machines (Laptops)",   "unit": "UNIT", "unit_price": (450, 1800)},
    {"hs":  "8517.12.00", "desc": "Telephones for Cellular Networks (Smartphones)",           "unit": "UNIT", "unit_price": (150, 850)},
    {"hs":  "8528.72.00", "desc": "LCD / LED Television Sets, Color",                         "unit": "UNIT", "unit_price": (120, 950)},
    {"hs":  "8708.29.00", "desc": "Body Parts and Accessories for Motor Vehicles",            "unit": "SET",  "unit_price": (80, 650)},
    {"hs":  "4011.10.00", "desc": "Pneumatic Tyres, of Rubber, for Motor Cars",               "unit": "UNIT", "unit_price": (35, 180)},
    {"hs":  "6110.20.00", "desc": "Jerseys, Pullovers and Similar Articles of Cotton",        "unit": "PCS",  "unit_price": (8, 45)},
    {"hs":  "7208.51.00", "desc": "Flat-Rolled Products of Iron / Non-Alloy Steel, ≥600mm", "unit": "MT",   "unit_price": (600, 1200)},
    {"hs":  "3004.90.00", "desc": "Medicaments for Therapeutic or Prophylactic Use",         "unit": "BOX",  "unit_price": (25, 280)},
    {"hs":  "8443.31.00", "desc": "Printing Machinery Used for Printing",                     "unit": "UNIT", "unit_price": (250, 2500)},
    {"hs":  "3901.10.00", "desc": "Polyethylene Having a Specific Gravity < 0.94",           "unit": "KG",   "unit_price": (1.2, 3.5)},
    {"hs":  "0901.11.00", "desc": "Coffee, Not Roasted, Not Decaffeinated",                  "unit": "KG",   "unit_price": (4, 12)},
    {"hs":  "8504.40.00", "desc": "Static Converters (Power Supply Units)",                   "unit": "UNIT", "unit_price": (45, 380)},
    {"hs":  "9401.61.00", "desc": "Seats with Wooden Frames, Upholstered",                   "unit": "UNIT", "unit_price": (55, 320)},
    {"hs":  "8542.31.00", "desc": "Electronic Integrated Circuits, Processors and Controllers","unit":"UNIT", "unit_price": (12, 450)},
    {"hs":  "6203.42.00", "desc": "Men's Trousers and Breeches of Cotton",                   "unit": "PCS",  "unit_price": (6, 35)},
]

VESSELS = [
    ("MV Maersk Seletar",    "0123W", "TCKU"),
    ("MV MSC Gaia",          "216E",  "MSCU"),
    ("MV CMA CGM Coral",     "0134N", "CMAU"),
    ("MV Evergreen Universe", "119W", "EVGR"),
    ("MV Yang Ming Wellness", "023E", "YMLU"),
    ("MV Hapag Jakarta Exp.", "112N", "HLCU"),
    ("MV OOCL Indonesia",     "218E", "OOLU"),
    ("MV Pacific Star",       "041W", "APHU"),
    ("MV Cosco Harmony",      "097E", "COSU"),
    ("MV Wan Hai 232",        "183N", "WHLC"),
]

PORTS = [
    "Busan, Republic of Korea",
    "Shanghai, China",
    "Guangzhou, China",
    "Shenzhen, China",
    "Tianjin, China",
    "Qingdao, China",
    "Yokohama, Japan",
    "Osaka, Japan",
    "Rotterdam, Netherlands",
    "Singapore",
    "Port Klang, Malaysia",
    "Ho Chi Minh City, Vietnam",
]

def _date(offset_days=0):
    base = datetime(2026, random.randint(1, 6), random.randint(1, 28))
    d = base + timedelta(days=offset_days)
    return d.strftime("%d %B %Y")

def _container(prefix):
    return f"{prefix}{''.join(str(random.randint(0,9)) for _ in range(7))}"

def _invoice_no(prefix="INV"):
    return f"{prefix}-2026-{random.randint(1000,9999)}"

def _seal():
    return f"SL{random.randint(100000,999999)}"


# ── Styles ────────────────────────────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()
    return {
        "title":    ParagraphStyle("title",    parent=base["Normal"], fontSize=16, fontName="Helvetica-Bold",  alignment=TA_CENTER, spaceAfter=2),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontSize=9,  fontName="Helvetica",       alignment=TA_CENTER, spaceAfter=1, textColor=colors.HexColor("#555555")),
        "docno":    ParagraphStyle("docno",    parent=base["Normal"], fontSize=10, fontName="Helvetica-Bold",  alignment=TA_RIGHT,  spaceAfter=2),
        "h2":       ParagraphStyle("h2",       parent=base["Normal"], fontSize=8,  fontName="Helvetica-Bold",  spaceAfter=1, textColor=colors.HexColor("#1B4FBF")),
        "body":     ParagraphStyle("body",     parent=base["Normal"], fontSize=8,  fontName="Helvetica",       spaceAfter=1, leading=11),
        "small":    ParagraphStyle("small",    parent=base["Normal"], fontSize=7,  fontName="Helvetica",       textColor=colors.HexColor("#666666")),
        "footer":   ParagraphStyle("footer",   parent=base["Normal"], fontSize=7,  fontName="Helvetica-Oblique", alignment=TA_CENTER, textColor=colors.HexColor("#888888")),
        "total":    ParagraphStyle("total",    parent=base["Normal"], fontSize=9,  fontName="Helvetica-Bold",  alignment=TA_RIGHT),
    }

BLUE  = colors.HexColor("#1B4FBF")
LBLUE = colors.HexColor("#E8EEF9")
GRAY  = colors.HexColor("#F5F5F5")
DGRAY = colors.HexColor("#333333")


# ── Commercial Invoice ────────────────────────────────────────────────────────
def make_commercial_invoice(idx: int, out_dir: Path):
    imp_name, imp_addr = random.choice(IMPORTERS)
    exp_name, exp_addr = random.choice(EXPORTERS)
    good = random.choice(GOODS)
    vessel_name, voyage, shipping_prefix = random.choice(VESSELS)
    port_load = random.choice(PORTS)
    inv_date = _date()
    inv_no = _invoice_no("INV")
    container = _container(shipping_prefix)
    qty = random.randint(20, 500)
    unit_price = round(random.uniform(*good["unit_price"]), 2)
    total = round(qty * unit_price, 2)
    net_wt  = round(qty * random.uniform(0.3, 8), 2)
    gross_wt = round(net_wt * 1.08, 2)
    cartons = max(1, qty // random.randint(5, 20))

    st = _styles()
    out_path = out_dir / f"commercial_invoice_{idx:02d}.pdf"
    doc = SimpleDocTemplate(str(out_path), pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    story = []

    # Header
    story.append(Paragraph("COMMERCIAL INVOICE", st["title"]))
    story.append(Paragraph("Faktur Komersial", st["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=4))

    # Doc info row
    info_data = [
        [Paragraph(f"<b>Invoice No.:</b> {inv_no}", st["body"]),
         Paragraph(f"<b>Date:</b> {inv_date}", st["body"])],
        [Paragraph(f"<b>Payment Terms:</b> {random.choice(['T/T 30 Days','L/C at Sight','T/T in Advance'])}", st["body"]),
         Paragraph(f"<b>Currency:</b> USD", st["body"])],
    ]
    story.append(Table(info_data, colWidths=["55%","45%"], style=TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GRAY),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ])))
    story.append(Spacer(1, 5))

    # Shipper / Consignee
    parties = [
        [Paragraph("<b>SHIPPER / EXPORTER</b>", st["h2"]),
         Paragraph("<b>CONSIGNEE / IMPORTER</b>", st["h2"])],
        [Paragraph(f"<b>{exp_name}</b><br/>{exp_addr}", st["body"]),
         Paragraph(f"<b>{imp_name}</b><br/>{imp_addr}", st["body"])],
    ]
    story.append(Table(parties, colWidths=["50%","50%"], style=TableStyle([
        ("BOX",      (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID",(0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("BACKGROUND",(0,0),(-1,0), LBLUE),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ])))
    story.append(Spacer(1, 5))

    # Shipping info
    ship_data = [
        [Paragraph("<b>PORT OF LOADING</b>", st["h2"]),
         Paragraph("<b>PORT OF DISCHARGE</b>", st["h2"]),
         Paragraph("<b>VESSEL / VOYAGE</b>", st["h2"]),
         Paragraph("<b>CONTAINER NO.</b>", st["h2"])],
        [Paragraph(port_load, st["body"]),
         Paragraph("Cikarang Dry Port, Bekasi, Indonesia", st["body"]),
         Paragraph(f"{vessel_name}<br/>Voy. {voyage}", st["body"]),
         Paragraph(f"<b>{container}</b><br/>Seal: {_seal()}", st["body"])],
    ]
    story.append(Table(ship_data, colWidths=["25%","30%","25%","20%"], style=TableStyle([
        ("BOX",      (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID",(0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("BACKGROUND",(0,0),(-1,0), LBLUE),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ])))
    story.append(Spacer(1, 6))

    # Goods table
    story.append(Paragraph("DESCRIPTION OF GOODS", st["h2"]))
    goods_header = [
        Paragraph("<b>No.</b>", st["body"]),
        Paragraph("<b>HS Code</b>", st["body"]),
        Paragraph("<b>Description of Goods</b>", st["body"]),
        Paragraph("<b>Qty</b>", st["body"]),
        Paragraph("<b>Unit</b>", st["body"]),
        Paragraph("<b>Unit Price (USD)</b>", st["body"]),
        Paragraph("<b>Amount (USD)</b>", st["body"]),
    ]
    goods_row = [
        "1",
        good["hs"],
        Paragraph(good["desc"], st["body"]),
        str(qty),
        good["unit"],
        f"{unit_price:,.2f}",
        f"{total:,.2f}",
    ]
    goods_total = [
        "", "", Paragraph("<b>TOTAL</b>", st["body"]), str(qty), "", "",
        Paragraph(f"<b>USD {total:,.2f}</b>", st["body"]),
    ]
    story.append(Table(
        [goods_header, goods_row, goods_total],
        colWidths=["5%","12%","33%","8%","8%","17%","17%"],
        style=TableStyle([
            ("BOX",       (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ("INNERGRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDDDDD")),
            ("BACKGROUND",(0,0), (-1,0),  BLUE),
            ("TEXTCOLOR", (0,0), (-1,0),  colors.white),
            ("BACKGROUND",(0,-1),(-1,-1), LBLUE),
            ("ALIGN",     (3,0), (-1,-1), "CENTER"),
            ("LEFTPADDING",(0,0),(-1,-1), 6),
            ("TOPPADDING",(0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ])
    ))
    story.append(Spacer(1, 5))

    # Weight summary
    wt_data = [
        [Paragraph(f"<b>Total Cartons:</b> {cartons} CTN", st["body"]),
         Paragraph(f"<b>Net Weight:</b> {net_wt:,.2f} KG", st["body"]),
         Paragraph(f"<b>Gross Weight:</b> {gross_wt:,.2f} KG", st["body"])],
    ]
    story.append(Table(wt_data, colWidths=["33%","33%","34%"], style=TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), GRAY),
        ("BOX",(0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ])))
    story.append(Spacer(1, 10))

    # Signature
    sig_data = [
        [Paragraph(f"<b>Declared by / Dinyatakan oleh:</b>", st["body"]),
         Paragraph("", st["body"])],
        [Paragraph(f"<br/><br/>___________________________________<br/>{exp_name}<br/>{_date()}", st["small"]),
         Paragraph(f"<b>Stamp / Cap:</b><br/><br/><br/>", st["small"])],
    ]
    story.append(Table(sig_data, colWidths=["55%","45%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ])))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This document is issued for customs clearance purposes at Cikarang Dry Port, Bekasi, Indonesia. "
        "All information stated herein is true and correct to the best of our knowledge.",
        st["footer"]
    ))

    doc.build(story)
    return out_path


# ── Bill of Lading ────────────────────────────────────────────────────────────
def make_bill_of_lading(idx: int, out_dir: Path):
    imp_name, imp_addr = random.choice(IMPORTERS)
    exp_name, exp_addr = random.choice(EXPORTERS)
    good = random.choice(GOODS)
    vessel_name, voyage, shipping_prefix = random.choice(VESSELS)
    port_load = random.choice(PORTS)
    bl_date = _date()
    bl_no = _invoice_no("BL")
    container = _container(shipping_prefix)
    qty = random.randint(10, 300)
    gross_wt = round(qty * random.uniform(1.5, 25), 2)
    cbm = round(qty * random.uniform(0.02, 0.5), 2)
    cartons = max(1, qty // random.randint(4, 15))

    st = _styles()
    out_path = out_dir / f"bill_of_lading_{idx:02d}.pdf"
    doc = SimpleDocTemplate(str(out_path), pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    story = []

    story.append(Paragraph("BILL OF LADING", st["title"]))
    story.append(Paragraph("Konosemen — Non-Negotiable Copy", st["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=4))

    # B/L number + date
    bl_info = [
        [Paragraph(f"<b>B/L No.:</b> {bl_no}", st["body"]),
         Paragraph(f"<b>Date of Issue:</b> {bl_date}", st["body"]),
         Paragraph(f"<b>Freight:</b> {random.choice(['PREPAID','COLLECT'])}", st["body"])],
    ]
    story.append(Table(bl_info, colWidths=["40%","35%","25%"], style=TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), GRAY),
        ("BOX",(0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID",(0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ])))
    story.append(Spacer(1, 5))

    # Parties
    party_data = [
        [Paragraph("<b>SHIPPER</b>", st["h2"]),
         Paragraph("<b>CONSIGNEE</b>", st["h2"])],
        [Paragraph(f"<b>{exp_name}</b><br/>{exp_addr}", st["body"]),
         Paragraph(f"<b>{imp_name}</b><br/>{imp_addr}", st["body"])],
        [Paragraph("<b>NOTIFY PARTY</b>", st["h2"]), ""],
        [Paragraph(f"{imp_name}<br/>{imp_addr.split(',')[0]}", st["body"]), ""],
    ]
    story.append(Table(party_data, colWidths=["50%","50%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID",(0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ("BACKGROUND",(0,0),(-1,0), LBLUE),
        ("BACKGROUND",(0,2),(-1,2), LBLUE),
        ("SPAN",(0,2),(1,2)), ("SPAN",(0,3),(1,3)),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ])))
    story.append(Spacer(1, 5))

    # Voyage details
    voy_data = [
        [Paragraph("<b>PORT OF LOADING</b>", st["h2"]),
         Paragraph("<b>PORT OF DISCHARGE</b>", st["h2"]),
         Paragraph("<b>PLACE OF DELIVERY</b>", st["h2"])],
        [Paragraph(port_load, st["body"]),
         Paragraph("Tanjung Priok, Jakarta, Indonesia", st["body"]),
         Paragraph("Cikarang Dry Port, Bekasi, Indonesia", st["body"])],
        [Paragraph("<b>VESSEL</b>", st["h2"]),
         Paragraph("<b>VOYAGE NO.</b>", st["h2"]),
         Paragraph("<b>FLAG</b>", st["h2"])],
        [Paragraph(vessel_name, st["body"]),
         Paragraph(voyage, st["body"]),
         Paragraph(random.choice(["Republic of Korea","Panama","Liberia","Singapore","Japan"]), st["body"])],
    ]
    story.append(Table(voy_data, colWidths=["34%","33%","33%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID",(0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ("BACKGROUND",(0,0),(-1,0), LBLUE),
        ("BACKGROUND",(0,2),(-1,2), LBLUE),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ])))
    story.append(Spacer(1, 5))

    # Container details
    cont_data = [
        [Paragraph("<b>CONTAINER NO.</b>", st["h2"]),
         Paragraph("<b>SEAL NO.</b>", st["h2"]),
         Paragraph("<b>CONTAINER SIZE</b>", st["h2"]),
         Paragraph("<b>CONTAINER TYPE</b>", st["h2"])],
        [Paragraph(f"<b>{container}</b>", st["body"]),
         Paragraph(_seal(), st["body"]),
         Paragraph(random.choice(["20' Standard","40' Standard","40' High Cube"]), st["body"]),
         Paragraph("DRY VAN", st["body"])],
    ]
    story.append(Table(cont_data, colWidths=["30%","25%","25%","20%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID",(0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ("BACKGROUND",(0,0),(-1,0), BLUE),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ])))
    story.append(Spacer(1, 5))

    # Cargo description
    story.append(Paragraph("DESCRIPTION OF CARGO / URAIAN BARANG", st["h2"]))
    cargo_hdr = [Paragraph(f"<b>{h}</b>", st["body"]) for h in
                 ["No. of Packages","Kind of Packages","Description of Goods","HS Code","Gross Weight (KG)","Measurement (CBM)"]]
    cargo_row = [
        str(cartons), "CARTONS",
        Paragraph(good["desc"], st["body"]),
        good["hs"],
        f"{gross_wt:,.2f}",
        f"{cbm:,.3f}",
    ]
    story.append(Table([cargo_hdr, cargo_row], colWidths=["15%","15%","25%","13%","17%","15%"],
        style=TableStyle([
            ("BOX",(0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ("INNERGRID",(0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
            ("BACKGROUND",(0,0),(-1,0), BLUE),
            ("TEXTCOLOR",(0,0),(-1,0), colors.white),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1), 4),
            ("TOPPADDING",(0,0),(-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ])))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"SAID TO CONTAIN: {cartons} ({cartons} {('carton' if cartons==1 else 'cartons').upper()}) ONLY",
        st["small"]
    ))
    story.append(Spacer(1, 8))

    # Clause
    story.append(Paragraph(
        "RECEIVED by the Carrier the Goods in apparent good order and condition unless otherwise noted herein. "
        "SHIPPED on board the Vessel for carriage to the Port of Discharge or so near thereto as the Vessel may safely get, "
        "and to be delivered in the like good order and condition. This Bill of Lading is issued for customs clearance "
        "purposes at Cikarang Dry Port (CDP), Bekasi, West Java, Indonesia.",
        st["small"]
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"Issued at {port_load.split(',')[0]} on {bl_date}  ·  "
        f"As Carrier: {random.choice(['Maersk Line','MSC Mediterranean Shipping','CMA CGM','Evergreen Marine','Yang Ming Marine'])}",
        st["footer"]
    ))
    doc.build(story)
    return out_path


# ── Packing List ──────────────────────────────────────────────────────────────
def make_packing_list(idx: int, out_dir: Path):
    imp_name, imp_addr = random.choice(IMPORTERS)
    exp_name, exp_addr = random.choice(EXPORTERS)
    good = random.choice(GOODS)
    vessel_name, voyage, shipping_prefix = random.choice(VESSELS)
    port_load = random.choice(PORTS)
    pl_date = _date()
    pl_no   = _invoice_no("PL")
    inv_no  = _invoice_no("INV")
    container = _container(shipping_prefix)

    # Multiple carton rows
    num_rows = random.randint(2, 5)
    rows_data = []
    total_ctns = total_net = total_gross = total_cbm = 0
    for i in range(num_rows):
        ctns = random.randint(5, 80)
        net_u  = round(random.uniform(0.3, 8), 2)
        gross_u = round(net_u * 1.08, 2)
        cbm_u  = round(random.uniform(0.01, 0.4), 3)
        rows_data.append([
            str(i+1), str(ctns), good["unit"],
            f"{net_u*ctns:,.2f}", f"{gross_u*ctns:,.2f}", f"{cbm_u*ctns:,.3f}",
        ])
        total_ctns  += ctns
        total_net   += net_u * ctns
        total_gross += gross_u * ctns
        total_cbm   += cbm_u * ctns

    st = _styles()
    out_path = out_dir / f"packing_list_{idx:02d}.pdf"
    doc = SimpleDocTemplate(str(out_path), pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    story = []

    story.append(Paragraph("PACKING LIST", st["title"]))
    story.append(Paragraph("Daftar Kemasan", st["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=4))

    # Header info
    hdr = [
        [Paragraph(f"<b>Packing List No.:</b> {pl_no}", st["body"]),
         Paragraph(f"<b>Date:</b> {pl_date}", st["body"]),
         Paragraph(f"<b>Invoice No.:</b> {inv_no}", st["body"])],
    ]
    story.append(Table(hdr, colWidths=["38%","30%","32%"], style=TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), GRAY),
        ("BOX",(0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID",(0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ])))
    story.append(Spacer(1, 5))

    # Parties
    parties = [
        [Paragraph("<b>EXPORTER / PENGIRIM</b>", st["h2"]),
         Paragraph("<b>IMPORTER / PENERIMA</b>", st["h2"])],
        [Paragraph(f"<b>{exp_name}</b><br/>{exp_addr}", st["body"]),
         Paragraph(f"<b>{imp_name}</b><br/>{imp_addr}", st["body"])],
    ]
    story.append(Table(parties, colWidths=["50%","50%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID",(0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ("BACKGROUND",(0,0),(-1,0), LBLUE),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ])))
    story.append(Spacer(1, 5))

    # Shipping info
    ship = [
        [Paragraph("<b>VESSEL / KAPAL</b>", st["h2"]),
         Paragraph("<b>PORT OF LOADING</b>", st["h2"]),
         Paragraph("<b>PORT OF DISCHARGE</b>", st["h2"]),
         Paragraph("<b>CONTAINER NO.</b>", st["h2"])],
        [Paragraph(f"{vessel_name}<br/>Voy. {voyage}", st["body"]),
         Paragraph(port_load, st["body"]),
         Paragraph("Cikarang Dry Port, Bekasi, Indonesia", st["body"]),
         Paragraph(f"<b>{container}</b>", st["body"])],
    ]
    story.append(Table(ship, colWidths=["25%","25%","30%","20%"], style=TableStyle([
        ("BOX",(0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID",(0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ("BACKGROUND",(0,0),(-1,0), LBLUE),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ])))
    story.append(Spacer(1, 6))

    # Goods description
    story.append(Paragraph(
        f"<b>Description of Goods / Uraian Barang:</b>  {good['desc']}  (HS Code: {good['hs']})",
        st["body"]
    ))
    story.append(Spacer(1, 4))

    # Packing table
    pk_hdr = [Paragraph(f"<b>{h}</b>", st["body"]) for h in
              ["No.", "No. of Cartons", "Unit", "Net Weight (KG)", "Gross Weight (KG)", "Measurement (CBM)"]]
    pk_total = [
        Paragraph("<b>TOTAL</b>", st["body"]),
        Paragraph(f"<b>{total_ctns}</b>", st["body"]),
        "",
        Paragraph(f"<b>{total_net:,.2f}</b>", st["body"]),
        Paragraph(f"<b>{total_gross:,.2f}</b>", st["body"]),
        Paragraph(f"<b>{total_cbm:,.3f}</b>", st["body"]),
    ]
    table_rows = [pk_hdr] + [[Paragraph(c, st["body"]) for c in r] for r in rows_data] + [pk_total]
    story.append(Table(table_rows, colWidths=["7%","17%","12%","22%","22%","20%"],
        style=TableStyle([
            ("BOX",(0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ("INNERGRID",(0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
            ("BACKGROUND",(0,0),(-1,0), BLUE),
            ("TEXTCOLOR",(0,0),(-1,0), colors.white),
            ("BACKGROUND",(0,-1),(-1,-1), LBLUE),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("LEFTPADDING",(0,0),(-1,-1), 4),
            ("TOPPADDING",(0,0),(-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("ROWBACKGROUNDS",(0,1),(-1,-2),[colors.white, GRAY]),
        ])))
    story.append(Spacer(1, 8))

    # Signature
    story.append(Paragraph(
        f"<b>Declared by / Dinyatakan oleh:</b><br/><br/>"
        f"___________________________________<br/>{exp_name}<br/>{pl_date}",
        st["small"]
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Packing list ini diterbitkan untuk keperluan pabean di Cikarang Dry Port (CDP), Bekasi, Jawa Barat, Indonesia. "
        "This packing list is issued for customs clearance at Cikarang Dry Port.",
        st["footer"]
    ))
    doc.build(story)
    return out_path


# ── Convert PDF to PNG ────────────────────────────────────────────────────────
def pdf_to_png(pdf_path: Path, out_dir: Path) -> Path:
    """Convert PDF to 300 DPI PNG in out_dir — lossless, Tesseract-ready."""
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(str(pdf_path), dpi=300, first_page=1, last_page=1)
        png_path = out_dir / pdf_path.with_suffix(".png").name
        images[0].save(str(png_path), "PNG")
        return png_path
    except Exception as e:
        print(f"  Warning: PNG conversion skipped for {pdf_path.name}: {e}")
        return None


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import shutil

    N = 100  # documents per type

    DOC_TYPES = [
        ("commercial_invoice", make_commercial_invoice),
        ("bill_of_lading",     make_bill_of_lading),
        ("packing_list",       make_packing_list),
    ]

    # Create clean folder structure: sample_docs/{type}/docs/ and /images/
    for doc_type, _ in DOC_TYPES:
        docs_dir   = BASE_OUT / doc_type / "docs"
        images_dir = BASE_OUT / doc_type / "images"
        # Clear existing files
        if docs_dir.exists():   shutil.rmtree(docs_dir)
        if images_dir.exists(): shutil.rmtree(images_dir)
        docs_dir.mkdir(parents=True)
        images_dir.mkdir(parents=True)

    print(f"Generating {N} documents per type  ({N * 3} PDFs + {N * 3} PNGs)\n")

    total_pdf = total_png = 0

    for doc_type, maker in DOC_TYPES:
        docs_dir   = BASE_OUT / doc_type / "docs"
        images_dir = BASE_OUT / doc_type / "images"
        label = doc_type.replace("_", " ").title()
        print(f"  {label} (100):")

        for i in range(1, N + 1):
            # Generate PDF into docs/
            pdf_path = maker(i, docs_dir)
            total_pdf += 1

            # Convert to PNG into images/
            png_path = pdf_to_png(pdf_path, images_dir)
            if png_path:
                total_png += 1

            if i % 10 == 0:
                print(f"    {i}/{N} done...")

        print()

    print(f"Done — {total_pdf} PDFs  +  {total_png} PNGs")
    print(f"Output: {BASE_OUT}\n")
    print("Folder structure:")
    for doc_type, _ in DOC_TYPES:
        pdfs = list((BASE_OUT / doc_type / "docs").glob("*.pdf"))
        pngs = list((BASE_OUT / doc_type / "images").glob("*.png"))
        print(f"  {doc_type}/")
        print(f"    docs/    — {len(pdfs)} PDFs")
        print(f"    images/  — {len(pngs)} PNGs")
