# FlashPort

> **Snap. Extract. Declare.**
> AI-powered customs declaration automation for Cikarang Dry Port.

AI Open Innovation Challenge 2026 — Case 1 | Team: Teknik Logistik, President University

---

## The Problem

Field operators at Cikarang Dry Port spend 2–4 hours manually transcribing data from trade documents into the CEISA customs system. Errors lead to Jalur Merah (Red Lane) rejections, delays, and demurrage costs.

**FlashPort cuts that to under 3 minutes** — a mobile camera scan triggers a full AI pipeline that extracts, validates, and pre-scores every declaration before the manager even opens the dashboard.

---

## How It Works

```
Operator photographs         Backend processes            Manager reviews
a trade document      →      in seconds            →      and submits
(offline-capable)
                             OCR (Tesseract)
                             ↓
                             spaCy NER
                             ↓
                             Keyword proximity extraction
                             ↓
                             Regex fallback
                             ↓
                             XGBoost risk score + SHAP
                             ↓
                             WebSocket → live dashboard
```

1. Operator opens the Flutter app, selects document type, and photographs a Bill of Lading, Commercial Invoice, or Packing List — even with no internet.
2. The document is queued in SQLite and auto-syncs when the network returns.
3. The backend runs Tesseract OCR, preprocesses with OpenCV, then passes the text through a 3-stage extraction pipeline driven by a live database of field definitions.
4. XGBoost scores the declaration 0–100 for CEISA rejection risk. SHAP explains every point added or removed.
5. The web dashboard receives the record instantly via WebSocket. The manager reviews, edits fields, approves or rejects.
6. On approval, the declaration is submitted to CEISA. The operator receives a push notification with the result.

---

## Key Capabilities

**AI Extraction**
- 3-stage pipeline: spaCy NER → keyword proximity → regex fallback
- 27 built-in fields across all 3 document types, with per-doc-type scoping (Bill of Lading is never penalised for missing Invoice Value)
- Admin-configurable: add new fields, keywords, and risk weights from the dashboard — no code changes needed

**Risk Scoring**
- XGBoost classifier trained on 6,000 synthetic declarations — 93.7% cross-validation accuracy, 100% red lane recall
- SHAP explainability returned with every prediction: each feature's contribution shown as a bar chart
- Watchlist auto-elevates risk for flagged importers, exporters, or HS codes
- Manager-configured rules for custom field/condition/boost logic

**Manager Dashboard**
- Live WebSocket feed — new declarations appear instantly
- Full-resolution document image beside the extracted fields
- Inline field editing, approve/reject with note, batch CEISA submission
- Field Schema page: add or reconfigure extraction fields without touching code
- SLA monitoring, audit trail, operator management, CSV export

**Mobile**
- Offline-first: camera capture queues locally, syncs automatically
- 4-step status timeline per scan: Scanned → Synced → Reviewed → Approved/Rejected
- FCM push notifications for every review decision

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  MOBILE (Flutter)       BACKEND (FastAPI)       WEB (React)     │
│                                                                 │
│  Camera / File      →   OpenCV + Tesseract  →   Dashboard       │
│  Offline SQLite     →   3-stage Extractor   →   Detail Panel    │
│  Auto-sync          →   XGBoost + SHAP      →   Field Schema    │
│  FCM Notifications  →   Watchlist / Rules   →   CEISA Portal    │
│                     →   PostgreSQL          →   Audit Trail      │
└─────────────────────────────────────────────────────────────────┘
```

| Layer | Technology |
|---|---|
| Mobile | Flutter 3.x + Dart — iOS + Android |
| Backend | Python 3.11 + FastAPI — 42 REST endpoints + WebSocket |
| OCR | Tesseract `eng+ind` + OpenCV preprocessing |
| Field extraction | spaCy NER → keyword proximity (DB-driven) → regex fallback |
| Risk scoring | XGBoost 400 trees · 93.7% CV accuracy · SHAP explainability |
| Database | PostgreSQL 15 — stores documents, fields, audit logs, field definitions |
| Web | React 18 + Tailwind CSS 3 |
| Auth | JWT HS256 (manager) + API Key (mobile) |
| Push | Firebase FCM HTTP v1 |

---

## Document Fields

| Document Type | Fields Extracted |
|---|---|
| **All types** | Importer, Exporter, Container ID, Description of Goods |
| **Commercial Invoice** | HS Code, Invoice Value, Invoice Number, Invoice Date, Country of Origin, Quantity, Unit Price, Incoterms, Payment Terms, Port of Discharge |
| **Bill of Lading** | B/L Number, Vessel Name, Port of Loading, Port of Discharge, Voyage Number, Seal Number, ETA, Freight Terms |
| **Packing List** | Net Weight, Gross Weight, Carton Count, CBM, Package Type, Marks & Numbers |

Each field has an `extraction_keywords` list covering English, Bahasa Indonesia, and common abbreviations (avg 14 keywords per field). Admins can add or edit fields from the **Field Schema** page without redeploying.

---

## CEISA Risk Lanes

| Lane | Score | Outcome |
|---|---|---|
| 🟢 Green | < 30 | Auto-clearance — immediate release |
| 🟡 Yellow | 30–69 | Document verification required |
| 🔴 Red | ≥ 70 | Physical inspection — held at port |

---

## Quick Start

### Prerequisites

- PostgreSQL 15 (`brew install postgresql@15`)
- Python 3.11+, Node.js 18+, Flutter 3.x
- Tesseract OCR (`brew install tesseract`)

### 1 — Database

```bash
psql postgres -c "CREATE USER flashport WITH PASSWORD 'flashport';"
psql postgres -c "CREATE DATABASE flashport OWNER flashport;"
psql -U flashport -d flashport -f docker/postgres/init.sql
```

### 2 — Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Train the AI models (≈ 2 min)
python scripts/generate_training_data.py
python scripts/train_risk_model.py
python scripts/generate_ner_training.py
python scripts/train_ner_model.py

# Start
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first start the backend seeds operators, validation rules, and all 27 field definitions automatically.

### 3 — Web Dashboard

```bash
cd web
npm install && npm run dev
# → http://localhost:3000
```

Login: `manager` / `flashport2026`

### 4 — Mobile

```bash
cd mobile
flutter pub get && flutter run
```

| Employee ID | PIN |
|---|---|
| CDP-001 | 1234 |
| CDP-002 | 5678 |
| CDP-003 | 9012 |

> **Physical device:** set Server URL in the login screen to `http://[YOUR-MAC-IP]:8000`
> Find your IP: `ipconfig getifaddr en0`

---

## Project Structure

```
flashport/
├── mobile/
│   └── lib/
│       ├── screens/        camera, preview, result, home, login
│       ├── services/       sync, database, operator, backend_config
│       ├── models/         scan_record
│       └── widgets/        scan_tile
│
├── backend/
│   ├── app/
│   │   ├── api/            42 routes across 14 routers
│   │   ├── models/         9 SQLAlchemy models
│   │   ├── services/       ocr, extractor, validator, risk_scorer, fcm, audit
│   │   └── core/           ceisa_gateway (mock)
│   ├── scripts/            generate_training_data.py · train_risk_model.py
│   │                       generate_ner_training.py · train_ner_model.py
│   ├── data/               training_declarations.csv · sample_docs/
│   └── models/             risk_model.xgb · ner_model/
│
├── web/
│   └── src/
│       ├── components/     19 components
│       └── hooks/          useAuth · useDeclarations · useFieldDefs · useAPI
│
├── docs/                   System Breakdown · Proposal · How It Works
├── CLAUDE.md               Developer context
└── README.md
```

---

## API

Full interactive docs at `http://localhost:8000/docs`

| Group | Routes |
|---|---|
| Auth | `POST /auth/login` · `/auth/operator/login` |
| Sync | `POST /sync` |
| Declarations | `GET · PATCH · POST /declarations/{id}` |
| CEISA | `POST /ceisa/submit` · `/ceisa/batch-submit` · `GET /ceisa/submissions` |
| Field Definitions | `GET · POST · PATCH · DELETE /field-definitions` |
| Field Validation | `GET · POST · PATCH · DELETE /field-validation-rules` |
| Operators | `GET · POST · PATCH · DELETE /operators` |
| Watchlist | `GET · POST · DELETE /watchlist` |
| Risk Rules | `GET · POST · PATCH · DELETE /risk-rules` |
| HS Codes | `GET · POST · DELETE /hs-codes` · `GET /hs-codes/validate/{code}` |
| Reports | `GET /sla` · `GET /audit` · `GET /export/declarations.csv` |

---

## Team

| Name | Role |
|---|---|
| Bayu Pratama Putra Gunawan | Project Manager & AI Engineer |
| Myat Min Thu | Mobile Developer (Flutter) |
| Matthew Nazim | Backend & API Integration |
| Jonathan Gifford | UI/UX Designer |

---

*Built for the AI Open Innovation Challenge 2026 — Cikarang Dry Port, Indonesia.*
