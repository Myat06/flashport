from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.api import auth, audit, ceisa, declarations, export, field_definitions, field_validation_rules, hs_codes, operators, risk_rules, sla, sync, watchlist, ws
from app.api.auth import hash_pin, verify_token

# Import all models so create_all picks up every table
from app.models import declaration  # noqa: F401
from app.models import operator as operator_model  # noqa: F401
from app.models import audit as audit_model  # noqa: F401
from app.models import watchlist as watchlist_model  # noqa: F401
from app.models import risk_rule as risk_rule_model  # noqa: F401
from app.models import hs_code as hs_code_model  # noqa: F401
from app.models import field_validation_rule as field_validation_rule_model  # noqa: F401
from app.models import field_definition as field_definition_model            # noqa: F401

Base.metadata.create_all(bind=engine)


def _seed_operators() -> None:
    from app.models.operator import Operator

    db = SessionLocal()
    try:
        if db.query(Operator).count() > 0:
            return
        seed = [
            ("CDP-001", "Ahmad Fauzi", "1234"),
            ("CDP-002", "Budi Santoso", "5678"),
            ("CDP-003", "Citra Dewi", "9012"),
        ]
        for emp_id, name, pin in seed:
            db.add(Operator(employee_id=emp_id, name=name, pin_hash=hash_pin(pin)))
        db.commit()
    finally:
        db.close()


def _seed_validation_rules() -> None:
    from app.models.field_validation_rule import FieldValidationRule

    db = SessionLocal()
    try:
        if db.query(FieldValidationRule).count() > 0:
            return
        builtin = [
            ("HS Code — 8-digit format",       "hs_code",       "regex",      "critical",  r"^\d{4}\.?\d{2}\.?\d{2,4}$",          None,   None,    None, None, "HS code must be 8-digit format (e.g. 8471.30.10)"),
            ("HS Code — required",             "hs_code",       "required",   "critical",  None,                                   None,   None,    None, None, "HS code is required for CEISA submission"),
            ("Importer — required",            "importer",      "required",   "critical",  None,                                   None,   None,    None, None, "Importer name is required"),
            ("Invoice Value — currency format","invoice_value", "regex",      "critical",  r"(USD|EUR|SGD|CNY|IDR|JPY)\s*[\d,]+", None,   None,    None, None, "Invoice value must include a currency code (e.g. USD 75,000)"),
            ("Container ID — ISO 6346",        "container_id",  "regex",      "critical",  r"^[A-Z]{4}\d{7}$",                    None,   None,    None, None, "Container ID must be 4 uppercase letters + 7 digits (ISO 6346)"),
            ("Net Weight — valid range",       "net_weight",    "range",      "important", None,                                   "0.01", "20000", None, None, "Net weight must be between 0.01 and 20,000 kg"),
            ("Gross Weight — valid range",     "gross_weight",  "range",      "important", None,                                   "0.01", "20000", None, None, "Gross weight must be between 0.01 and 20,000 kg"),
            ("Exporter — required",            "exporter",      "required",   "important", None,                                   None,   None,    None, None, "Exporter name should be provided"),
            ("Vessel Name — max length",       "vessel_name",   "max_length", "optional",  None,                                   None,   None,    None, 50,   "Vessel name must not exceed 50 characters"),
        ]
        for name, field, rtype, priority, pattern, minv, maxv, allowed, maxlen, errmsg in builtin:
            db.add(FieldValidationRule(
                name=name, field_name=field, rule_type=rtype, priority=priority,
                pattern=pattern, min_val=minv, max_val=maxv,
                allowed_values=allowed, max_length=maxlen,
                error_message=errmsg, is_active=True, is_builtin=True,
            ))
        db.commit()
    finally:
        db.close()


def _seed_field_definitions() -> None:
    """Seed built-in field definitions with doc-type applicability.

    applicable_doc_types legend (None = all doc types):
      CI     = commercial_invoice
      BOL    = bill_of_lading
      PL     = packing_list
      CI_BOL = "commercial_invoice,bill_of_lading"  (both, but not PL)

    On every startup this also patches extraction_keywords and applicable_doc_types
    on existing rows so deployments always get the latest keyword lists.
    """
    from app.models.field_definition import FieldDefinition

    CI     = "commercial_invoice"
    BOL    = "bill_of_lading"
    PL     = "packing_list"
    CI_BOL = "commercial_invoice,bill_of_lading"
    ALL    = None  # NULL → every doc type

    db = SessionLocal()
    try:
        # fmt: off
        # Columns: field_key, display_label, priority, extraction_keywords, risk_weight, sort_order, applicable_doc_types
        seed = [

            # ── Fields present on ALL three document types ────────────────────
            ("importer", "Importer / Consignee", "critical",
             "Importer,Consignee,Importir,Penerima,Pembeli,Consigned To,"
             "Ship To,Bill To,Notify Party,Bought By,Buyer,To,Recipient,"
             "Received By,Kepada,Ditujukan Kepada,Consignee Name",
             15, 1, ALL),

            ("exporter", "Exporter / Shipper", "important",
             "Exporter,Shipper,Eksportir,Pengirim,Seller,Vendor,Shipped By,From,"
             "Manufacturer,Sold By,Issued By,Dikirim Oleh,Penjual,"
             "Perusahaan Pengirim,Beneficiary,Company",
             8, 2, ALL),

            ("container_id", "Container ID", "critical",
             "Container No,Container ID,Cont No,No. Container,Cont. No.,"
             "CNTR No,Container Number,Box No,Nomor Kontainer,"
             "Nomor Peti Kemas,Peti Kemas,No. Cont",
             10, 3, ALL),

            ("description", "Description of Goods", "optional",
             "Description,Description of Goods,Goods Description,Commodity,"
             "Uraian Barang,Keterangan Barang,Nama Barang,Item Description,"
             "Details,Particulars,Nature of Goods,Product Description,Item,Goods",
             2, 4, ALL),

            # ── Commercial Invoice ────────────────────────────────────────────
            ("hs_code", "HS Code", "critical",
             "HS Code,H.S. Code,H.S,HS,HTS Code,Harmonized Code,Tariff Code,"
             "Pos Tarif,Kode Tarif,No. HS,Kode HS,BTN,BTBMI,Customs Code,"
             "Customs Tariff,Tariff Number,HS Number",
             20, 5, CI),

            ("invoice_value", "Invoice Value", "critical",
             "Invoice Value,Total Value,Amount,Total Amount,Nilai Faktur,"
             "Nilai Invoice,Grand Total,Total Invoice,Total,Sub Total,Subtotal,"
             "Invoice Total,Amount Due,Total Due,Net Amount,Amount Payable,"
             "Nilai Total,Jumlah,Total Price",
             10, 6, CI),

            ("invoice_number", "Invoice Number", "important",
             "Invoice No,Invoice Number,No. Faktur,Nomor Faktur,Inv No,Invoice #,"
             "No Inv,SI No,Sales Invoice No,Commercial Invoice No,CI No,No CI,"
             "Proforma Invoice No,P/I No,Reference No,Ref No,Doc No",
             5, 7, CI),

            ("invoice_date", "Invoice Date", "important",
             "Invoice Date,Date of Invoice,Tanggal Faktur,Tanggal Invoice,"
             "Date,Tgl,Issued Date,Issue Date,Tanggal,Date of Issue,Inv Date",
             3, 8, CI),

            ("country_of_origin", "Country of Origin", "important",
             "Country of Origin,COO,Origin Country,Negara Asal,"
             "Country of Manufacture,Made in,Manufactured in,Origin,"
             "Produced in,Country of Production,Place of Origin",
             8, 9, CI),

            ("quantity", "Total Quantity", "important",
             "Quantity,Qty,Total Qty,Total Quantity,Jumlah,Jumlah Barang,"
             "Pcs,Units,No. of Pieces,Number of Pieces,Nos,Total Units,"
             "Total Pcs,Total Items,Item Qty",
             5, 10, CI),

            ("unit_price", "Unit Price", "optional",
             "Unit Price,Price per Unit,Harga Satuan,Unit Cost,Price Each,"
             "Per Unit,Each,Rate,Price/Unit,Unit Rate",
             3, 11, CI),

            ("incoterms", "Incoterms / Delivery Terms", "optional",
             "Incoterms,Trade Terms,Delivery Terms,Terms,Syarat Pengiriman,"
             "Payment and Delivery Terms,Trade Condition,Sale Terms,"
             "Shipment Terms,FOB,CIF,CFR,EXW,DDP,DAP,FCA",
             2, 12, CI),

            ("payment_terms", "Payment Terms", "optional",
             "Payment Terms,Terms of Payment,Cara Pembayaran,Syarat Pembayaran,"
             "Payment Method,Mode of Payment,Payment Condition,Settlement Terms,"
             "Remittance Terms,T/T,L/C,LC,D/P,D/A",
             2, 13, CI),

            # ── Bill of Lading ────────────────────────────────────────────────
            ("bl_number", "B/L Number", "critical",
             "B/L No,BL No,Bill of Lading No,Bill of Lading Number,B.L. No,"
             "No. B/L,No. BL,Nomor B/L,House B/L,HBL,Master B/L,MBL,"
             "Airway Bill,AWB No,No. AWB,Waybill No",
             10, 14, BOL),

            ("vessel_name", "Vessel / Ship Name", "critical",
             "Vessel,Ship,Vessel Name,Nama Kapal,By Vessel,Per Kapal,Carrier,"
             "M/V,MV,Mother Vessel,Feeder Vessel,V/V,On Board,Ocean Vessel,Kapal,"
             "Pre Carriage Vessel,Pre-Carriage by,Vessel and Voyage",
             10, 15, BOL),

            ("port_of_origin", "Port of Loading", "critical",
             "Port of Origin,Port of Loading,POL,Pelabuhan Muat,Origin Port,"
             "From Port,Loading Port,Place of Loading,Place of Origin,"
             "Port of Shipment,Loaded at,Shipped From,Place of Receipt,"
             "Port of Receipt,POR,Place of Issue",
             8, 16, BOL),

            ("voyage_number", "Voyage Number", "optional",
             "Voyage No,Voyage,Voy No,Voy,Trip No,No. Voyage,V/N,"
             "Voyage Number,Voyage/Trip,Rotation No",
             2, 17, BOL),

            ("seal_number", "Seal Number", "important",
             "Seal No,Seal Number,No. Segel,Container Seal,Seal,Segel,"
             "CSNO,C/S No,Seal & Serial No,Customs Seal,Official Seal",
             5, 18, BOL),

            ("eta", "ETA / Arrival Date", "optional",
             "ETA,Estimated Time of Arrival,Expected Arrival,Arrival Date,"
             "Expected Date of Arrival,Due Date,Expected ETA,Est. Arrival,"
             "Arrival,Date of Arrival",
             2, 19, BOL),

            ("freight_terms", "Freight Terms", "optional",
             "Freight,Ocean Freight,Freight Terms,Freight Prepaid,Freight Collect,"
             "Prepaid,Collect,Bayar Di Sini,Bayar Di Sana,Freight & Charges,"
             "Sea Freight,Air Freight,Freight Charges",
             2, 20, BOL),

            # ── Shared between Commercial Invoice + Bill of Lading ────────────
            ("port_of_discharge", "Port of Discharge / Destination", "important",
             "Port of Discharge,POD,Destination Port,Port of Destination,"
             "Pelabuhan Tujuan,Discharge Port,Final Destination,Place of Delivery,"
             "Delivery Port,Port of Delivery,Destination,To Port,Arrival Port",
             5, 21, CI_BOL),

            # ── Packing List ──────────────────────────────────────────────────
            ("net_weight", "Net Weight", "critical",
             "Net Weight,Nett Weight,Net Wt,Net Wt.,Berat Bersih,Berat Neto,"
             "N.W.,NW,Total Net Weight,Total Nett Weight,NW KG,Net Kg,Net W/T",
             10, 22, PL),

            ("gross_weight", "Gross Weight", "critical",
             "Gross Weight,Gross Wt,Gross Wt.,Berat Kotor,G.W.,GW,"
             "Total Gross Weight,GW KG,Gross Kg,Total Weight,G/W,Gross W/T",
             8, 23, PL),

            ("carton_count", "Carton / Package Count", "important",
             "Carton,Cartons,Ctns,CTN,No. of Cartons,Jumlah Karton,Koli,"
             "Packages,Pkgs,No of Pkgs,No of Packages,Packs,Boxes,Box,"
             "No. of Boxes,No. of Pkgs,Qty of Cartons,Total Packages,"
             "Total Cartons,Pieces,Pcs,No. of Pieces",
             5, 24, PL),

            ("cbm", "Volume / CBM", "optional",
             "CBM,Measurement,Volume,Cubic Meter,M3,Total Volume,Total CBM,"
             "Total Measurement,Meas,Ukuran,Cubic Metre,M/T,Volume CBM,"
             "Cubic Meters,CU.M",
             3, 25, PL),

            ("package_type", "Package Type", "optional",
             "Package Type,Packing Type,Type of Package,Jenis Kemasan,Packing,"
             "Kind of Package,Pack Type,Packaging,Type of Packing,Pack,Kind,"
             "Type of Packages",
             2, 26, PL),

            ("marks_numbers", "Marks & Numbers", "optional",
             "Marks & Numbers,Marks and Numbers,Shipping Marks,Mark & No,"
             "Tanda,Marks,No Marks,No Mark,Container Mark,Mark,Shipping Mark,"
             "Marks & Nos,Marks/Nos,Package Mark",
             2, 27, PL),
        ]
        # fmt: on

        existing = {r.field_key: r for r in db.query(FieldDefinition).all()}
        changed  = False

        for field_key, label, priority, kws, risk_weight, sort_order, doc_types in seed:
            if field_key in existing:
                fd      = existing[field_key]
                updated = False
                # Patch applicable_doc_types and keywords on every startup so
                # existing databases always get the latest lists.
                if fd.applicable_doc_types != doc_types:
                    fd.applicable_doc_types = doc_types
                    updated = True
                if fd.extraction_keywords != kws:
                    fd.extraction_keywords = kws
                    updated = True
                if updated:
                    changed = True
            else:
                db.add(FieldDefinition(
                    field_key=field_key, display_label=label, priority=priority,
                    extraction_keywords=kws, risk_weight=risk_weight,
                    sort_order=sort_order, applicable_doc_types=doc_types,
                    is_active=True, is_builtin=True,
                ))
                changed = True

        if changed:
            db.commit()
    finally:
        db.close()


_seed_operators()
_seed_validation_rules()
_seed_field_definitions()

app = FastAPI(
    title="FlashPort API",
    description="AI-powered customs declaration backend — Cikarang Dry Port",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_PROTECTED = ("/sync", "/declarations", "/ceisa", "/audit", "/watchlist", "/risk-rules", "/field-validation-rules", "/field-definitions", "/hs-codes", "/operators", "/sla", "/export")


@app.middleware("http")
async def auth_check(request: Request, call_next):
    # Allow CORS preflight through — browser sends OPTIONS before every request
    if request.method == "OPTIONS":
        return await call_next(request)

    if not any(request.url.path.startswith(p) for p in _PROTECTED):
        return await call_next(request)

    # Accept X-API-Key (mobile) or Bearer JWT (web dashboard)
    if request.headers.get("X-API-Key", "") == settings.api_key:
        return await call_next(request)

    bearer = request.headers.get("Authorization", "")
    if bearer.startswith("Bearer ") and verify_token(bearer[7:]):
        return await call_next(request)

    return JSONResponse(status_code=401, content={"detail": "Unauthorized"})


app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(declarations.router)
app.include_router(ceisa.router)
app.include_router(ws.router)
app.include_router(audit.router)
app.include_router(watchlist.router)
app.include_router(risk_rules.router)
app.include_router(hs_codes.router)
app.include_router(operators.router)
app.include_router(sla.router)
app.include_router(export.router)
app.include_router(field_definitions.router)
app.include_router(field_validation_rules.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "flashport-backend"}
