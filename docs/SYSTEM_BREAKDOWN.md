# FlashPort — System Breakdown (Updated June 2026)

**AI Open Innovation Challenge 2026 — Case 1: Cikarang Dry Port**
Team: Teknik Logistik | President University
Final Deadline: 31 August 2026

---

## 1. System Overview

FlashPort automates customs declaration preparation for Cikarang Dry Port (CDP) by combining mobile document capture, a multi-stage AI pipeline, and a professional manager dashboard. The system eliminates manual data entry, pre-scores declarations for CEISA rejection risk, and gives managers full visibility and control before submission.

### 1.1 Problem Statement

Field operators at CDP manually transcribe data from trade documents (Commercial Invoice, Bill of Lading, Packing List) into the CEISA customs system. This takes 2–4 hours per declaration, is error-prone, and frequently leads to Jalur Merah (Red Lane) rejections due to missing or mistyped fields.

### 1.2 Solution Summary

| Stage | Before | After FlashPort |
|---|---|---|
| Data collection | Manual transcription | Mobile camera / file upload |
| Field extraction | Human reading | 3-stage AI pipeline: spaCy NER → keyword proximity → regex |
| Field configuration | Code change required | Admin UI — add/edit fields, keywords, doc-type scope |
| Risk assessment | None | XGBoost AI scorer + SHAP explainability |
| Manager review | Manual email chain | Pro web dashboard — Approve / Reject |
| CEISA submission | Manual portal | One-click or batch from dashboard |
| Processing time | 2–4 hours | Under 3 minutes |

---

## 2. Architecture

### 2.1 Three-Layer System

```
FIELD LAYER — Flutter Mobile App (iOS + Android)
- Offline-first: camera capture or file attachment (JPG, PNG, PDF)
- Saves locally as Pending when offline
- Auto-syncs when network available
- Real-time status timeline: Scanned -> Synced -> Approved/Rejected
- FCM push notifications for all review decisions
- Clear Data button for demo resets
        |
        | HTTPS POST /sync (base64 image)
        v
PROCESSING LAYER — FastAPI Backend (Python 3.11)
  Document Input
  - Digital PDF  : pypdf direct text extraction (no OCR needed)
  - Photo/Image  : OpenCV preprocess -> Tesseract OCR (eng+ind)

  Field Extraction (Three-Stage, data-driven from field_definitions table)
  - Stage 1: spaCy NER — generic entity types (MONEY, ORG, GPE → mapped to field keys)
  - Stage 2: Keyword proximity — each field has extraction_keywords; grabs value after keyword
  - Stage 3: Regex fallback — catches values by format pattern (HS, container ISO 6346, currency)

  Risk Scoring
  - XGBoost model (16 features, 93.7% CV accuracy, trained on 6,000 synthetic records)
  - SHAP explainability — per-feature score contribution returned with every prediction
  - Watchlist check — auto-elevates risk for flagged entities
  - Manager-configured DB rules — custom field/condition/boost
  - Dynamic field risk_weight — new admin-defined fields contribute automatically

  Storage and Events
  - PostgreSQL — all data + original document image stored
  - Audit log — every action tracked
  - WebSocket broadcast — live web dashboard feed
        |
        | REST API + WebSocket
        v
MANAGEMENT LAYER — React 18 Admin Dashboard
  Main: Overview | Declarations | Analysis | CEISA Portal
  Operations: SLA Dashboard | Operators | Watchlist | Risk Rules | Audit Trail
```

### 2.2 Technology Stack

| Component | Technology | Notes |
|---|---|---|
| Mobile | Flutter 3.x (Dart) | iOS + Android from one codebase |
| Mobile storage | SQLite (sqflite) | Offline-first local persistence |
| Backend | Python 3.11 + FastAPI | Async, 42 API endpoints |
| PDF text extraction | pypdf | Direct text from digital PDFs — no OCR |
| OCR engine | Tesseract eng+ind | For scanned/photo documents |
| Image preprocessing | OpenCV | Smart: skips aggressive processing for clean images |
| Field extraction Stage 1 | spaCy NER | Generic entity types (MONEY, ORG, GPE, DATE) mapped to field keys |
| Field extraction Stage 2 | Keyword proximity | Per-field keyword lists from DB; grabs value after each keyword |
| Field extraction Stage 3 | Python Regex | Format-based fallback (HS code, container ISO 6346, currency) |
| Field configuration | `field_definitions` DB table | 27 built-in fields; admin can add more without code changes |
| Risk scoring | XGBoost (400 trees) | 93.7% cross-validation accuracy; trained on 6,000 synthetic samples |
| Explainability | SHAP TreeExplainer | 16 per-feature contributions per prediction |
| Database | PostgreSQL 15 | Local install |
| Web frontend | React 18 + Tailwind CSS 3 | Sidebar layout, 10 pages incl. Field Schema admin |
| Push notifications | Firebase FCM HTTP v1 | Approve/reject + CEISA lane results |
| Auth | JWT HS256 + API Key | 8h manager sessions, operator PIN login |

---

## 3. Mobile Application

### 3.1 Offline-First Upload Flow

```
1. Operator logs in with Employee ID + PIN
2. Select document type (Commercial Invoice / Bill of Lading / Packing List)
3. Take photo OR attach file (JPG, PNG, PDF)
4. Preview screen shows:
   - Document image with green Attached badge
   - File name + size
   - Document ready to upload confirmation card
5. Tap Upload & Sync
6. Upload progress animation:
   - Step 1: Preparing document...
   - Step 2: Uploading to server...
   - Step 3: Running OCR & AI analysis...
7. Result:
   - Online  -> Result screen (risk score, fields, CEISA readiness)
   - Offline -> Saved as Pending, auto-syncs when connected
```

### 3.2 Scan History Status Timeline

Each scan tile shows a mini progress indicator:

```
Scanned  ->  Synced  ->  Reviewed  ->  Approved
                                    ->  Rejected
```

### 3.3 Push Notifications

| Event | Title |
|---|---|
| Manager approved | Declaration Approved |
| Manager rejected | Declaration Rejected |
| CEISA Green Lane | CEISA: Green Lane |
| CEISA Yellow Lane | CEISA: Yellow Lane |
| CEISA Red Lane | CEISA: Red Lane |

### 3.4 Physical Device Setup

For physical iOS/Android devices, the Server URL must be set to the Mac's local IP:

```
http://[MAC-IP]:8000   (find with: ipconfig getifaddr en0)
```

iOS requires `NSAllowsArbitraryLoads = true` in Info.plist (already set) to allow local HTTP connections.

---

## 4. Backend Processing Pipeline

### 4.1 Two-Path Document Ingestion

**Path A — Digital PDF** (generated documents, digital forms)
```
base64 PDF -> pypdf.PdfReader -> clean structured text -> NER + Regex
(No OCR needed — reads text layer directly, much more accurate for tables)
```

**Path B — Photo or Scanned Image** (real mobile camera photos)
```
base64 JPG/PNG -> decode -> OpenCV smart preprocessing
                             |
                    Check white pixel ratio:
                    > 55% white -> grayscale only (already clean)
                    <= 55% white -> grayscale -> denoise -> adaptive threshold -> deskew
                             |
                    Tesseract OCR (eng+ind, --psm 6) -> NER + Regex
```

### 4.2 Three-Stage Field Extraction (Data-Driven)

All fields are defined in the `field_definitions` DB table. The admin can add new fields in the Field Schema page — extraction, validation, and risk scoring all update automatically.

**Stage 1 — spaCy NER**
- Handles generic entity types: MONEY → invoice_value, ORG → importer/exporter, GPE → port_of_origin, DATE → invoice_date, CARDINAL → quantity/carton_count
- Covers ~11 mappable entity types; new custom fields bypass this stage

**Stage 2 — Keyword Proximity** (primary for most fields)
- Each field definition has an `extraction_keywords` list (avg 14 keywords per field)
- Scanner finds the keyword in OCR text, grabs the value immediately after
- Covers English labels (CONSIGNEE, VESSEL), Indonesian (PENERIMA, KAPAL), and abbreviations (POL, BL No, GW)
- Per-doc-type filtering: a Bill of Lading scan loads only BoL + ALL fields — it is never penalised for missing HS Code or Invoice Value

**Stage 3 — Regex Fallback**
- Catches values by format pattern regardless of label
- HS code: `\d{4}\.\d{2}\.\d{2}`, Container: `[A-Z]{4}\d{7}`, Currency: `(USD|IDR|EUR)\s*[\d,]+`
- Validates all extracted values (rejects dates as weights, wrong container formats)

### 4.3 Risk Scoring

XGBoost model uses 16 features (trained on 6,000 synthetic records, 93.7% CV accuracy):

| Feature | Importance |
|---|---|
| high_value_no_container (>USD 50k, no container, CI only) | 32.3% |
| is_restricted_hs (weapons/chemicals HS prefix) | 16.2% |
| confidence_score (OCR quality: high/medium/low) | 15.9% |
| has_importer | 13.2% |
| has_hs_code | 5.7% |
| has_container_id | 2.9% |
| hs_high_scrutiny (electronics, petroleum categories) | 2.5% |
| has_exporter | 2.3% |
| document_type_enc | 1.8% |
| + 7 more features | 7.2% |

Score → Lane: Green < 30 | Yellow 30–70 | Red ≥ 70

On top of XGBoost:
- Any admin-defined field (not in the core 16 features) adds its `risk_weight` if missing
- Watchlist hits add +25 per matched entity
- Manager-configured DB rules add their custom boost

SHAP values are returned with every prediction and shown as a bar chart in the dashboard — explaining exactly which features drove the risk score up or down.

---

## 5. AI Training Pipeline

### 5.1 XGBoost Risk Model

```bash
# Step 1: Generate 6,000 synthetic declarations (2,000 per doc type)
python scripts/generate_training_data.py
# -> data/training_declarations.csv
# Distribution: 76% Green / 14% Yellow / 10% Red  (realistic CDP throughput)
# 12 scenario profiles per doc type: clean, partial, missing fields, low confidence,
#   high value, restricted HS, scrutiny HS, multi-missing, etc.
# Uses: 40 real Indonesian PT importers, 40 foreign exporters, 33 HS codes,
#       25 vessels on Asia-Indonesia trade routes, 20 ports worldwide

# Step 2: Train model
python scripts/train_risk_model.py
# -> models/risk_model.xgb
# -> models/model_info.json
# CV accuracy: 93.7% (+/- 0.4%)
# Red recall: 100% (zero red declarations missed — class weight 3×)
```

### 5.2 spaCy NER Model

```bash
# Step 1: Generate 300 annotated examples
python scripts/generate_ner_training.py
# -> data/ner_training.spacy
# Covers: commercial invoice, bill of lading, packing list (English + Indonesian)

# Step 2: Train model
python scripts/train_ner_model.py
# -> models/ner_model/
# F1: 1.000 on all 11 entity types
# Early stopped at iteration 15
```

### 5.3 Sample Document Generation

```bash
python scripts/generate_sample_docs.py
# Generates: 100 PDFs + 100 PNGs per document type
# Output:
#   data/sample_docs/commercial_invoice/docs/   (100 PDFs)
#   data/sample_docs/commercial_invoice/images/ (100 PNGs, 300 DPI)
#   data/sample_docs/bill_of_lading/docs/
#   data/sample_docs/bill_of_lading/images/
#   data/sample_docs/packing_list/docs/
#   data/sample_docs/packing_list/images/
```

Sample documents use realistic data:
- 40 Indonesian PT company importers (Bekasi/Cikarang industrial zone)
- 40+ foreign exporters (Korea, China, Japan, USA, Germany)
- 33 real HS codes including restricted categories (weapons, chemicals)
- 10 major shipping line container prefixes
- 25 vessels on Asia-Indonesia trade routes
- 20 ports of origin worldwide

### 5.4 Retraining with Real Data

```bash
# Option A: Enrich synthetic data with real CEISA rejection records
# Edit scripts/generate_training_data.py to include real patterns, then:
python scripts/generate_training_data.py
python scripts/train_risk_model.py
# -> models/risk_model.xgb  (replaces current synthetic-trained model)

# Option B: Add real document images to sample_docs/ for NER improvement
python scripts/generate_ner_training.py
python scripts/train_ner_model.py

# Restart backend -- models reload automatically on startup
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 6. Web Dashboard

### 6.1 Pages

| Page | What it shows |
|---|---|
| Overview | Total / Pending / Approved / Rejected KPIs, lane distribution, recent activity |
| Declarations | Full table with date range filter, batch select, CSV export, approve/reject |
| Analysis | Risk histogram, OCR confidence breakdown, field extraction quality |
| CEISA Portal | All submissions with Green/Yellow/Red lane badges |
| SLA Dashboard | Avg review time, overdue declarations (>24h pending) |
| Operators | Add/deactivate field operators, reset PINs |
| Watchlist | Flag importers, exporters, HS codes for automatic risk elevation |
| Risk Rules | field + condition + value + boost_points, toggle on/off |
| Field Validation Rules | Per-field regex/range/required rules; dynamic dropdown from field definitions |
| Field Schema | Add/edit/delete extraction fields — keywords, risk weight, doc-type scope |
| Audit Trail | Every action: who did what, when, on which declaration |

### 6.2 Declaration Detail Panel

Click any row to open right slide-in panel:
- Original document image (fetched from DB on demand)
- Risk score bar + SHAP explanation chart
- Extraction method badge (spaCy NER / NER+Regex / Regex)
- All extracted fields editable inline — rendered dynamically from field_definitions, ordered by sort_order
- Flagged issues (missing critical fields, format violations)
- Approve / Reject with optional note (sends FCM push to operator)
- Re-run OCR button
- Submit to CEISA button (only when ceisa_ready = true)

---

## 7. Database Schema

### Core Tables

```
declarations       id, scan_id, document_type, operator_id, image_data,
                   tesseract_text, confidence_badge, risk_score, risk_badge,
                   flagged_fields, ceisa_ready, review_status, review_note,
                   reviewed_by, reviewed_at

declaration_fields declaration_id, field_name, field_value, is_edited

ceisa_submissions  declaration_id, jalur, response_code, response_message,
                   submitted_by, submitted_at

sync_logs          scan_id, device_id, image_size_bytes, sync_duration_ms
operators          employee_id, name, pin_hash, is_active
```

### Operations Tables (Added June 2026)

```
audit_logs              action, entity_type, entity_id, performed_by, detail, created_at
watchlist               entity_type, value, reason, is_active
risk_rules              field, condition, value, risk_boost, flag_label, is_active
hs_code_reference       code, description, category, is_restricted, restriction_note
```

### Level 3 Field Tables (Added June 2026)

```
field_definitions       field_key, display_label, priority, extraction_keywords,
                        risk_weight, sort_order, applicable_doc_types, is_active, is_builtin
                        -- applicable_doc_types: NULL=all, or "commercial_invoice",
                        --   "bill_of_lading", "packing_list", or comma-separated combo
                        -- 27 built-in fields seeded on startup; admins can add more

field_validation_rules  field_name, rule_type (regex/required/range/max_length),
                        pattern, min_val, max_val, error_message, is_active, is_builtin
```

**Seeded field definitions:**

| Applies to | Fields |
|---|---|
| All doc types | importer, exporter, container_id, description |
| Commercial Invoice | hs_code, invoice_value, invoice_number, invoice_date, country_of_origin, quantity, unit_price, incoterms, payment_terms |
| Bill of Lading | bl_number, vessel_name, port_of_origin, voyage_number, seal_number, eta, freight_terms |
| CI + BoL | port_of_discharge |
| Packing List | net_weight, gross_weight, carton_count, cbm, package_type, marks_numbers |

---

## 8. Running the System

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Web dashboard
cd web && npm run dev     # -> http://localhost:3000
# Login: manager / flashport2026

# Mobile (simulator)
cd mobile && flutter run

# Mobile (physical device)
# 1. Get Mac IP: ipconfig getifaddr en0
# 2. In app login screen -> Server URL -> http://[IP]:8000
# 3. Login: CDP-001 / 1234
```

---

## 9. Phase 2 — August 2026

| Item | Status | Action |
|---|---|---|
| XGBoost risk scorer | ✅ Done | Trained on 6,000 synthetic samples, 93.7% CV accuracy, active as primary scorer |
| Dynamic field system | ✅ Done | 27 fields seeded; admin can add/edit/delete via Field Schema page |
| Real CEISA H2H | Pending | Request API credentials from Cikarang Dry Port; replace mock gateway with live HTTP calls |
| FCM push notifications | Pending | Firebase console → Service Accounts → download JSON → set FCM_SERVICE_ACCOUNT_JSON in .env |
| NER retrain on real docs | Optional | Use real scanned document images to improve Stage 1 extraction accuracy |
