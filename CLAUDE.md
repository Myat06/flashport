# FlashPort — CLAUDE.md

This file gives Claude Code the full context needed to work on FlashPort without rederiving it from scratch.

---

## Project Identity

FlashPort is an AI-powered customs declaration automation platform built for the AI Open Innovation Challenge 2026 (Case 1 — Cikarang Dry Port). It is a monorepo with three independent services.

**Final deadline:** 31 August 2026 — full working prototype with live CEISA integration.

**Team:** Teknik Logistik, President University

---

## Monorepo Layout

```
flashport/
├── mobile/       Flutter app — offline-first document scanning
├── backend/      FastAPI Python server — all business logic
├── web/          React 18 admin dashboard
├── docker/       postgres init.sql
└── docker-compose.yml   (not used — PostgreSQL runs locally)
```

---

## Architecture Rules

### Mobile (Flutter)
- No on-device OCR. `ocr_service.dart` deleted. Backend Tesseract is the only OCR engine.
- Offline flow: take photo / attach file → save as pending in SQLite → sync when connected.
- Online flow: take photo / attach file → confirm → backend OCR → result screen.
- FCM push notifications sent when manager approves/rejects or CEISA result arrives.
- Scan tile shows a 4-step status timeline: Scanned → Synced → Reviewed → Approved/Rejected.

### Backend (FastAPI)
- Tesseract OCR (`eng+ind`) is the only OCR engine — source of truth for all extraction.
- `compute_confidence()` always receives empty `ml_kit_text` → returns `(0.85, "high")`.
- Field extraction, validation, and risk scoring are ALL driven by the `field_definitions` DB table (Level 3 — no code changes needed when fields change).
- Risk scorer: XGBoost primary (trained) → rule-based fallback if model missing.
- Every action (scan, approve, reject, CEISA submit, reprocess) is logged to `audit_logs`.
- Watchlist check runs on every sync — auto-elevates risk if importer/exporter matched.
- Document image (`image_b64`) is stored in `declarations.image_data` for web viewing.

### Web Dashboard (React + Tailwind)
- Left sidebar navigation with two groups: Main and Operations.
- `StatsBar` always shows: Total / Pending / Approved / Rejected / CEISA Ready.
- Declarations shown as a table with batch checkboxes, filter tabs, and search.
- Click a row → right-side `DetailPanel` slides in: image + fields + approve/reject + CEISA.
- **Field Schema** page lets admins add/edit/delete fields, keywords, risk weights, and which doc type a field applies to — without any code changes.
- All text is English — no Bahasa Indonesia anywhere in the UI.

---

## Running the Project

### PostgreSQL (local, no Docker)
```bash
# Already set up — flashport DB exists at localhost:5432
# User: flashport / flashport
# To re-init schema: psql -U flashport -d flashport -f docker/postgres/init.sql
```

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Web
```bash
cd web
npm run dev    # http://localhost:3000 (or 3001 if 3000 is taken)
```

**Manager login:** `manager` / `flashport2026`

### Mobile
```bash
cd mobile
flutter run
```

### Tests
```bash
cd backend && pytest   # 14/14 passing
```

### Retrain XGBoost (if training data changes)
```bash
cd backend
source venv/bin/activate
python scripts/generate_training_data.py   # regenerates data/training_declarations.csv
python scripts/train_risk_model.py         # writes models/risk_model.xgb
```

---

## Stack Summary

| Layer | Tech | Notes |
|---|---|---|
| Mobile | Flutter 3.x + Dart | `mobile/` |
| Mobile OCR | **REMOVED** | No on-device OCR. Backend Tesseract only. |
| Backend | Python 3.11 + FastAPI | `backend/` |
| Backend OCR | Tesseract `eng+ind` | Source of truth. `/opt/homebrew/bin/tesseract` |
| Preprocessing | OpenCV | grayscale → threshold → deskew. PDF → image via pdf2image |
| Field Extraction | 3-stage pipeline | Stage 1: spaCy NER (generic entity types). Stage 2: keyword proximity from `field_definitions`. Stage 3: regex fallback by value pattern. All fields are data-driven — no hardcoded field names in extractor. |
| Risk Scoring | XGBoost (primary) + SHAP | Trained on 6,000 synthetic samples, 93.7% CV accuracy. 16-feature vector. Rule-based fallback if model file missing. `models/risk_model.xgb`. |
| Database | PostgreSQL 15 | Local install (no Docker) |
| Web | React 18 + Tailwind CSS 3 | `web/` |
| Auth | JWT (HS256) + API Key | 8h token expiry. Manager = JWT. Mobile = API Key. |
| Push | Firebase FCM HTTP v1 | Approve/reject + CEISA result notifications |

---

## Environment Variables

`backend/.env`:
```
DATABASE_URL=postgresql://flashport:flashport@localhost:5432/flashport
TESSERACT_CMD=/opt/homebrew/bin/tesseract
SECRET_KEY=changeme-use-a-long-random-string-in-production
API_KEY=changeme
MANAGER_USERNAME=manager
MANAGER_PASSWORD=flashport2026
FCM_SERVER_KEY=
FCM_PROJECT_ID=flashport-9870d
FCM_SERVICE_ACCOUNT_JSON=
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173
```

---

## Full API Reference (42 routes)

| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Manager JWT login |
| POST | `/auth/operator/login` | Operator PIN login (mobile) |
| POST | `/sync` | Mobile document sync — OCR, extract, score, store |
| POST | `/ocr/preview` | Quick OCR preview (optional pre-save check) |
| GET | `/declarations` | List all declarations with review_status |
| GET | `/declarations/{id}/image` | Fetch stored base64 document image |
| PATCH | `/declarations/{id}/field` | Edit an extracted field |
| PATCH | `/declarations/{id}/review` | Approve / reject with note + FCM push |
| POST | `/declarations/{id}/reprocess` | Re-run Tesseract OCR on stored image |
| POST | `/ceisa/submit` | Submit declaration to CEISA (single) |
| POST | `/ceisa/batch-submit` | Submit multiple declarations at once |
| GET | `/ceisa/submissions` | List all CEISA submissions |
| GET | `/operators` | List all field operators |
| POST | `/operators` | Add new operator |
| PATCH | `/operators/{employee_id}` | Update operator (name, active status) |
| POST | `/operators/{employee_id}/reset-pin` | Reset operator PIN |
| DELETE | `/operators/{employee_id}` | Deactivate operator |
| GET | `/watchlist` | List active watchlist entries |
| POST | `/watchlist` | Add importer/exporter/HS code to watchlist |
| DELETE | `/watchlist/{id}` | Remove watchlist entry |
| GET | `/watchlist/check` | Check if entity is on watchlist |
| GET | `/risk-rules` | List all custom risk rules |
| POST | `/risk-rules` | Create a risk rule |
| PATCH | `/risk-rules/{id}` | Update/toggle a rule |
| DELETE | `/risk-rules/{id}` | Delete a rule |
| GET | `/field-validation-rules` | List field validation rules |
| POST | `/field-validation-rules` | Create a validation rule |
| PATCH | `/field-validation-rules/{id}` | Update / toggle a rule |
| DELETE | `/field-validation-rules/{id}` | Delete a validation rule |
| GET | `/field-definitions` | List all field definitions (ordered by sort_order) |
| POST | `/field-definitions` | Add a custom field |
| PATCH | `/field-definitions/{id}` | Update a field definition |
| DELETE | `/field-definitions/{id}` | Delete a custom field (built-in fields are protected) |
| GET | `/hs-codes` | List HS code reference entries |
| GET | `/hs-codes/validate/{code}` | Validate an HS code |
| POST | `/hs-codes` | Add HS code to reference |
| DELETE | `/hs-codes/{code}` | Remove HS code from reference |
| GET | `/sla` | SLA metrics (avg review time, overdue, throughput) |
| GET | `/audit` | Audit log (filter by entity_id, entity_type) |
| GET | `/export/declarations.csv` | CSV export with optional filters |
| GET | `/ws` | WebSocket — live declaration feed |
| GET | `/health` | Health check |

---

## Database Schema

### Core Tables
- `declarations` — main record: OCR text, extracted fields summary, risk/confidence badges, `review_status`, `image_data`, `reviewed_by`
- `declaration_fields` — extracted key-value pairs linked to declaration
- `ceisa_submissions` — CEISA submission attempts and lane responses
- `sync_logs` — mobile sync events

### Operations Tables (added 2026-06-22)
- `audit_logs` — action, entity_type, entity_id, performed_by, detail, created_at
- `watchlist` — entity_type (importer/exporter/hs_code), value, reason, is_active
- `risk_rules` — field, condition, value, risk_boost, flag_label, is_active
- `hs_code_reference` — code, description, category, is_restricted, restriction_note
- `operators` — employee_id, name, pin_hash, is_active

### Level 3 Dynamic Field Tables (added 2026-06-26)
- `field_definitions` — field_key, display_label, priority, extraction_keywords, risk_weight, sort_order, applicable_doc_types, is_active, is_builtin
  - `applicable_doc_types`: NULL = all doc types; comma-separated = specific types (e.g. `"commercial_invoice,bill_of_lading"`)
  - Built-in fields cannot be deleted via API
  - 27 fields seeded on first startup covering all 3 doc types
- `field_validation_rules` — field_name, rule_type (regex/required/range/max_length), pattern, min_val, max_val, error_message, is_active, is_builtin

### Declaration review_status enum
`pending` → `approved` or `rejected` (manager can reset to `pending`)

---

## Backend Models

```
backend/app/models/
├── declaration.py              Declaration, DeclarationField, CeisaSubmission, SyncLog
│                               Enums: ConfidenceLevel, RiskLevel, ReviewStatus, JalurType, DocType
├── operator.py                 Operator
├── audit.py                    AuditLog
├── watchlist.py                WatchlistEntry
├── risk_rule.py                RiskRule
├── hs_code.py                  HsCodeReference
├── field_definition.py         FieldDefinition (27 seeded, admin can add more)
└── field_validation_rule.py    FieldValidationRule
```

---

## Level 3 — Dynamic Field Architecture

All field extraction, validation, and risk scoring are driven by the `field_definitions` DB table. Adding a new field in the admin UI automatically makes the system extract, validate, and score it — no code changes.

### Extraction pipeline (3 stages per field)
1. **spaCy NER** — catches generic entity types (MONEY→invoice_value, ORG→importer, GPE→port_of_origin, etc.). Only works for the 11 standard entity types. New custom fields bypass this stage entirely.
2. **Keyword proximity** — for each field_def, scans text for `extraction_keywords`, then grabs the value immediately after. This is where 90% of CI/BoL/PL fields are found.
3. **Regex fallback** — catches values by format pattern regardless of label (e.g. HS code pattern `\d{4}\.\d{2}\.\d{2}`, container ISO 6346 `[A-Z]{4}\d{7}`).

### Doc-type filtering
`_load_field_defs(db, doc_type)` in `sync.py` filters fields by `applicable_doc_types`:
- `NULL` → field applies to all 3 doc types
- `"commercial_invoice"` → only on CI scans
- `"bill_of_lading,commercial_invoice"` → both, but not PL

This means a BoL scan is NOT checked for missing HS Code or Invoice Value — they are simply not loaded.

### Risk scoring flow
1. **XGBoost** (primary) — 16-feature fixed vector → outputs green/yellow/red probability
2. **Dynamic risk_weight** — for every field NOT in the XGBoost feature set, apply `risk_weight` on top if the field is missing
3. **`_XGB_MANAGED_FIELDS`** = `{hs_code, invoice_value, container_id, importer, exporter, vessel_name, port_of_origin}` — these are already inside XGBoost; do not double-count
4. **Watchlist hits** — +25 per hit, always on top
5. **Manager DB rules** — `risk_rules` table, any condition/boost

### XGBoost model facts
- Training data: `backend/data/training_declarations.csv` — 6,000 synthetic records
- Generator: `backend/scripts/generate_training_data.py` — 12 scenario profiles × 3 doc types
- Trainer: `backend/scripts/train_risk_model.py` — 5-fold CV, class-weighted (red = 3×)
- CV accuracy: 93.7% ± 0.4%. Red recall: 100% (zero red declarations missed).
- Top features by importance: high_value_no_container (32%), is_restricted_hs (16%), confidence_score (16%), has_importer (13%)
- Model file: `backend/models/risk_model.xgb`
- Info/metadata: `backend/models/model_info.json`

---

## Seeded Field Definitions (27 total)

| Doc Type | Fields |
|---|---|
| ALL | importer, exporter, container_id, description |
| Commercial Invoice | hs_code, invoice_value, invoice_number, invoice_date, country_of_origin, quantity, unit_price, incoterms, payment_terms |
| Bill of Lading | bl_number, vessel_name, port_of_origin, voyage_number, seal_number, eta, freight_terms |
| CI + BoL | port_of_discharge |
| Packing List | net_weight, gross_weight, carton_count, cbm, package_type, marks_numbers |

Each field has `extraction_keywords` covering English, Bahasa Indonesia, and common abbreviations (avg 14 keywords per field).

---

## Web Components

```
web/src/
├── App.jsx                       Shell: sidebar + header + routing + detail panel
├── components/
│   ├── Sidebar.jsx               Fixed left nav — Main group + Operations group (Field Schema added)
│   ├── StatsBar.jsx              5 KPI cards: Total/Pending/Approved/Rejected/CEISA Ready
│   ├── DeclarationTable.jsx      Table with checkboxes, filter tabs, date range, search
│   ├── DetailPanel.jsx           Right slide-in: image + fields + approve/reject + CEISA + re-OCR
│   ├── DashboardView.jsx         Overview: KPIs + charts + recent activity
│   ├── AnalysisView.jsx          Risk distribution, flagged fields, doc type breakdown
│   ├── CeisaView.jsx             CEISA Portal — submission history with lane badges
│   ├── CeisaModal.jsx            Submit modal — shows lane result
│   ├── OperatorsView.jsx         Operator CRUD table + PIN reset
│   ├── WatchlistView.jsx         Add/remove watchlist entries
│   ├── RiskRulesView.jsx         Configure custom scoring rules
│   ├── FieldValidationRulesView.jsx  Validation rules — dynamic field dropdown from field_defs
│   ├── FieldDefinitionsView.jsx  Field Schema admin — add/edit/delete fields, keywords, doc-type
│   ├── SLAView.jsx               SLA metrics — daily throughput + overdue list
│   ├── AuditView.jsx             Full audit trail with colour-coded event types
│   ├── FieldEditor.jsx           Inline field editing inside detail panel (dynamic from field_defs)
│   ├── RiskBadge.jsx             Green/Yellow/Red lane badge
│   ├── ConfidenceBadge.jsx       High/Medium/Low OCR confidence badge
│   ├── LoginPage.jsx             Manager login form
│   └── Toast.jsx                 Notification toasts
└── hooks/
    ├── useAuth.js                JWT auth with localStorage + expiry check
    ├── useDeclarations.js        Declarations state + WebSocket + updateField + reviewDeclaration
    ├── useAPI.js                 Generic get/post/patch/del/download helper
    ├── useFieldDefs.js           Fetches /field-definitions with JWT; used in App.jsx
    └── useCeisaSubmissions.js    CEISA submissions fetch
```

---

## Mobile Screens & Services

```
mobile/lib/
├── screens/
│   ├── home_screen.dart          Scan list + logout + pending badge
│   ├── camera_screen.dart        Camera / file picker → PreviewScreen
│   ├── preview_screen.dart       Image + doc type + Confirm & Save
│   ├── result_screen.dart        Risk card + dynamic field list (driven by API response)
│   └── login_screen.dart         Operator employee ID + PIN login
├── services/
│   ├── sync_service.dart         Save to SQLite + upload to backend + FCM token
│   ├── database_service.dart     SQLite CRUD for scan_records
│   ├── operator_service.dart     Login, logout, employee ID, JWT token
│   └── backend_config.dart       Server URL (editable in login screen)
├── models/
│   └── scan_record.dart          ScanRecord, SyncStatus, DocumentType
└── widgets/
    └── scan_tile.dart            Scan list item + 4-step status timeline
```

---

## Data Contract

### Mobile → Backend (`POST /sync`)
```json
{
  "scan_id": "uuid-v4",
  "scanned_at": "2026-06-22T10:00:00Z",
  "document_type": "commercial_invoice | bill_of_lading | packing_list",
  "operator_id": "CDP-001",
  "fcm_token": "firebase-token",
  "ml_kit_text": "",
  "image_b64": "base64-encoded-compressed-image"
}
```

### Backend → Mobile (sync response)
```json
{
  "declaration_id": "uuid",
  "confidence_badge": "high | medium | low",
  "risk_score": 42,
  "risk_badge": "green | yellow | red",
  "extracted_fields": { "hs_code": "8471.30.00", "invoice_value": "USD 12,500", "..." : "..." },
  "flagged_fields": ["missing:country_of_origin"],
  "shap_values": [{ "feature": "has_importer", "label": "Importer identified", "shap_value": -0.32, "direction": "decrease" }],
  "ceisa_ready": true
}
```

`extracted_fields` is dynamic — it contains whatever fields were found for the given `document_type`. The mobile result screen renders all fields from `fields.entries` without hardcoding any field names.

---

## Risk Scoring Logic

### Primary: XGBoost (16 features)
1. Binary field presence: has_hs_code, has_invoice_value, has_container_id, has_importer, has_exporter, has_vessel, has_port
2. Missing field count (doc-type-aware — BoL is not penalised for missing invoice_value)
3. OCR confidence score (high=2, medium=1, low=0)
4. Document type encoding (CI=0, BoL=1, PL=2)
5. is_restricted_hs (weapons/chemicals)
6. invoice_value_log, is_high_value (>50k), is_very_high_value (>200k)
7. high_value_no_container (CI only)
8. hs_high_scrutiny (electronics, LCDs, petroleum prefixes)

Score formula: `int(proba[yellow] × 40 + proba[red] × 100)`, capped at 100.

### On top of XGBoost
- **Custom field penalties** — any field in `field_definitions` NOT in `_XGB_MANAGED_FIELDS`, if missing, adds `risk_weight` points
- **Watchlist hits** — +25 per matched importer/exporter/HS code
- **Manager DB rules** — `risk_rules` table (field/condition/value/boost)

### Badges
- green: score < 30
- yellow: 30 ≤ score < 70
- red: score ≥ 70

### Rule-based fallback (when XGBoost model file is absent)
Fully dynamic from `field_defs[].risk_weight` — no hardcoded field names.

---

## Audit Actions

| Action | Trigger |
|---|---|
| `declaration.created` | Every mobile sync |
| `declaration.approved` | Manager approves |
| `declaration.rejected` | Manager rejects |
| `declaration.pending` | Manager resets to pending |
| `declaration.reprocessed` | Manager triggers re-OCR |
| `ceisa.submitted` | Single or batch CEISA submit |

---

## What NOT to Do

- Do not add on-device OCR. `ocr_service.dart` has been deleted. All OCR is Tesseract on the backend.
- Do not use YOLO v8 or Gemini Vision — not in the System Breakdown (proposal only).
- Do not call any paid external APIs. Stack is 100% free/open-source.
- Do not hardcode credentials. Use `.env` files.
- Do not use Docker for the database — PostgreSQL runs locally.
- Do not re-add `google_mlkit_text_recognition` to `pubspec.yaml`.
- Do not hardcode field names in `extractor.py`, `validator.py`, or `risk_scorer.py` — all field logic is driven by the `field_definitions` DB table (Level 3). Add new fields via admin UI or the seed in `main.py`.
- Do not add fields to `_XGB_MANAGED_FIELDS` in `risk_scorer.py` unless you retrain the XGBoost model with those features in the feature vector.

---

## Credentials & Secrets

| Secret | Value | Where |
|---|---|---|
| Web dashboard login | `manager` / `flashport2026` | `backend/.env` |
| Backend API key (mobile) | `changeme` (change in prod) | `backend/.env` |
| JWT secret | `changeme-use-a-long-random-string-in-production` | `backend/.env` |
| Firebase Android config | placed | `mobile/android/app/google-services.json` |
| Firebase iOS config | placed | `mobile/ios/Runner/GoogleService-Info.plist` |
| FCM service account JSON | **not yet downloaded** | `backend/.env` → `FCM_SERVICE_ACCOUNT_JSON=` |

---

## Seeded Operators

Seeded on first backend start:
- CDP-001 / Ahmad Fauzi / PIN: 1234
- CDP-002 / Budi Santoso / PIN: 5678
- CDP-003 / Citra Dewi / PIN: 9012

## Seeded HS Code Reference (10 codes)
- Electronics (8471, 8517, 8542) — not restricted
- Weapons (9301, 9302) — restricted, require Ministry of Defense permit
- Chemicals (2710, 2711) — restricted, require energy ministry approval
- Textiles, Food & Beverage — not restricted

---

## Remaining Work (Phase 2 — August 2026)

1. **Real CEISA H2H Integration** — need API credentials from Cikarang Dry Port
   - Replace `backend/app/api/ceisa.py` mock gateway with real HTTP calls
   - Add `CEISA_API_URL`, `CEISA_CLIENT_ID`, `CEISA_SECRET` to `.env`

2. **FCM Service Account** — manual step (no code needed)
   - Firebase console → Project Settings → Service Accounts → Generate new private key
   - Save JSON content to `FCM_SERVICE_ACCOUNT_JSON` in `.env`
