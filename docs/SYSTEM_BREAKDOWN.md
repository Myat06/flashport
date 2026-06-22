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
| Field extraction | Human reading | spaCy NER + Regex pipeline |
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

  Field Extraction (Two-Stage NLP)
  - Stage 1: spaCy NER — context-aware, handles Indonesian labels
  - Stage 2: Regex fallback — fills any gaps from NER

  Risk Scoring
  - XGBoost model (16 features, 89.5% CV accuracy)
  - SHAP explainability — per-feature score contribution
  - Watchlist check — auto-elevates risk for flagged entities
  - Manager-configured DB rules — custom field/condition/boost

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
| Backend | Python 3.11 + FastAPI | Async, 36 API endpoints |
| PDF text extraction | pypdf | Direct text from digital PDFs — no OCR |
| OCR engine | Tesseract eng+ind | For scanned/photo documents |
| Image preprocessing | OpenCV | Smart: skips aggressive processing for clean images |
| Field extraction Stage 1 | spaCy NER (custom trained) | 11 entity types, 100% F1, English + Indonesian |
| Field extraction Stage 2 | Python Regex | Fallback + table-merge patterns |
| Risk scoring | XGBoost (300 trees) | 89.5% cross-validation accuracy |
| Explainability | SHAP TreeExplainer | 16 per-feature contributions per prediction |
| Database | PostgreSQL 15 | Local install |
| Web frontend | React 18 + Tailwind CSS 3 | Sidebar layout, 9 pages |
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

### 4.2 Two-Stage NLP Field Extraction

**Stage 1 — spaCy NER**
- Custom trained on 300 annotated customs document examples
- 11 entity types: HS_CODE, INVOICE_VALUE, CONTAINER_ID, IMPORTER, EXPORTER, NET_WEIGHT, GROSS_WEIGHT, VESSEL_NAME, PORT_OF_ORIGIN, INVOICE_NUMBER, CARTON_COUNT
- Handles both English labels (CONSIGNEE, SHIPPER) and Indonesian (PENERIMA, PENGIRIM)
- 100% F1 on development set

**Stage 2 — Regex Fallback**
- Runs only on fields NER missed
- Specialized patterns: OCR table-merge, TOTAL row weights, direct MV vessel pattern
- Validates all extracted values (rejects dates as weights, bare currency codes, wrong container formats)

### 4.3 Risk Scoring

XGBoost model uses 16 features:

| Feature | Importance |
|---|---|
| is_restricted_hs (weapons/chemicals HS) | 36.5% |
| hs_high_scrutiny (electronics, petroleum) | 10.7% |
| missing_field_count | 8.0% |
| has_port | 6.0% |
| has_container_id | 4.6% |
| high_value_no_container | 4.6% |
| has_hs_code | 4.5% |
| has_vessel | 4.0% |
| invoice_value_log | 4.0% |
| + 7 more features | 17.1% |

Score -> Lane: Green < 30 | Yellow 30-70 | Red > 70

SHAP values are returned with every prediction and shown as a bar chart in the dashboard — explaining exactly which features drove the risk score up or down.

---

## 5. AI Training Pipeline

### 5.1 XGBoost Risk Model

```bash
# Step 1: Generate 600 synthetic declarations
python scripts/generate_training_data.py
# -> data/training_declarations.csv
# Distribution: 395 Green / 127 Yellow / 78 Red (65/21/13%)
# Uses: real Indonesian PT company names, real HS codes, real vessel names

# Step 2: Train model
python scripts/train_risk_model.py
# -> models/risk_model.xgb
# -> models/model_info.json
# CV accuracy: 89.5% (+/- 3.9%)
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

### 5.4 Retraining with Real Data (August 2026)

```bash
# Replace training_declarations.csv with real company data, then:
python scripts/train_risk_model.py

# Add real document images to sample_docs/ then:
python scripts/generate_ner_training.py
python scripts/train_ner_model.py

# Restart backend -- models reload automatically
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 6. Web Dashboard

### 6.1 Pages

| Page | What it shows |
|---|---|
| Overview | Total / Pending / Approved / Rejected KPIs, lane distribution, recent activity |
| Declarations | Full table with filters, batch select, CSV export, approve/reject |
| Analysis | Risk histogram, OCR confidence breakdown, field extraction quality |
| CEISA Portal | All submissions with Green/Yellow/Red lane badges |
| SLA Dashboard | Avg review time, overdue declarations (>24h pending) |
| Operators | Add/deactivate field operators, reset PINs |
| Watchlist | Flag importers, exporters, HS codes for automatic risk elevation |
| Risk Rules | field + condition + value + boost_points, toggle on/off |
| Audit Trail | Every action: who did what, when, on which declaration |

### 6.2 Declaration Detail Panel

Click any row to open right slide-in panel:
- Original document image (fetched from DB on demand)
- Risk score bar + SHAP explanation chart
- Extraction method badge (spaCy NER / NER+Regex / Regex)
- All 11 fields editable inline
- Flagged issues
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
audit_logs         action, entity_type, entity_id, performed_by, detail, created_at
watchlist          entity_type, value, reason, is_active
risk_rules         field, condition, value, risk_boost, flag_label, is_active
hs_code_reference  code, description, category, is_restricted, restriction_note
```

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

| Item | Action |
|---|---|
| Real CEISA H2H | After company visit July 27-31, replace mock with live API |
| XGBoost retrain | Feed real rejection data from company into train_risk_model.py |
| NER retrain | Use real document scans from company into generate_ner_training.py |
| FCM activation | Firebase console -> Service Accounts -> download JSON -> set in .env |
