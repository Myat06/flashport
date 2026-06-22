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
- Risk scorer applies: baseline rules + manager-configured DB rules + watchlist hits.
- Every action (scan, approve, reject, CEISA submit, reprocess) is logged to `audit_logs`.
- Watchlist check runs on every sync — auto-elevates risk if importer/exporter matched.
- Document image (`image_b64`) is stored in `declarations.image_data` for web viewing.

### Web Dashboard (React + Tailwind)
- Left sidebar navigation with two groups: Main and Operations.
- `StatsBar` always shows: Total / Pending / Approved / Rejected / CEISA Ready.
- Declarations shown as a table with batch checkboxes, filter tabs, and search.
- Click a row → right-side `DetailPanel` slides in: image + fields + approve/reject + CEISA.
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
cd backend && pytest   # 12/12 passing
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
| Field Extraction | spaCy NER (deep learning) + Regex fallback | NER is primary, regex fills gaps. Model: `models/ner_model/` |
| Risk Scoring | XGBoost + SHAP explainability | `models/risk_model.xgb`. SHAP returned in every sync response. |
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

## Full API Reference (38 routes)

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

### New Tables (2026-06-22)
- `audit_logs` — action, entity_type, entity_id, performed_by, detail, created_at
- `watchlist` — entity_type (importer/exporter/hs_code), value, reason, is_active
- `risk_rules` — field, condition, value, risk_boost, flag_label, is_active
- `hs_code_reference` — code, description, category, is_restricted, restriction_note
- `operators` — employee_id, name, pin_hash, is_active

### Declaration review_status enum
`pending` → `approved` or `rejected` (manager can reset to `pending`)

---

## Backend Models

```
backend/app/models/
├── declaration.py    Declaration, DeclarationField, CeisaSubmission, SyncLog
│                     Enums: ConfidenceLevel, RiskLevel, ReviewStatus, JalurType, DocType
├── operator.py       Operator
├── audit.py          AuditLog
├── watchlist.py      WatchlistEntry
├── risk_rule.py      RiskRule
└── hs_code.py        HsCodeReference
```

---

## Web Components

```
web/src/
├── App.jsx                  Shell: sidebar + header + routing + detail panel
├── components/
│   ├── Sidebar.jsx          Fixed left nav — Main group + Operations group
│   ├── StatsBar.jsx         5 KPI cards always visible (Total/Pending/Approved/Rejected/CEISA)
│   ├── DeclarationTable.jsx Table with checkboxes, filter tabs, search
│   ├── DetailPanel.jsx      Right slide-in: image + fields + approve/reject + CEISA + re-OCR
│   ├── DashboardView.jsx    Overview: Pending/Approved/Rejected KPIs + charts + recent activity
│   ├── AnalysisView.jsx     Risk distribution, flagged fields, doc type breakdown
│   ├── CeisaView.jsx        CEISA Portal — submission history with lane badges
│   ├── CeisaModal.jsx       Submit modal — shows lane result
│   ├── OperatorsView.jsx    Operator CRUD table + PIN reset
│   ├── WatchlistView.jsx    Add/remove watchlist entries
│   ├── RiskRulesView.jsx    Configure custom scoring rules
│   ├── SLAView.jsx          SLA metrics — daily throughput + overdue list
│   ├── AuditView.jsx        Full audit trail with colour-coded event types
│   ├── FieldEditor.jsx      Inline field editing inside detail panel
│   ├── RiskBadge.jsx        Green/Yellow/Red lane badge
│   ├── ConfidenceBadge.jsx  High/Medium/Low OCR confidence badge
│   ├── LoginPage.jsx        Manager login form
│   └── Toast.jsx            Notification toasts
└── hooks/
    ├── useAuth.js            JWT auth with localStorage + expiry check
    ├── useDeclarations.js    Declarations state + WebSocket + updateField + reviewDeclaration
    ├── useAPI.js             Generic get/post/patch/del/download helper
    └── useCeisaSubmissions.js CEISA submissions fetch
```

---

## Mobile Screens & Services

```
mobile/lib/
├── screens/
│   ├── home_screen.dart      Scan list + logout + pending badge
│   ├── camera_screen.dart    Camera / file picker → PreviewScreen
│   ├── preview_screen.dart   Image + doc type + Confirm & Save
│   ├── result_screen.dart    Risk card + fields + Green/Yellow/Red lane
│   └── login_screen.dart     Operator employee ID + PIN login
├── services/
│   ├── sync_service.dart     Save to SQLite + upload to backend + FCM token
│   ├── database_service.dart SQLite CRUD for scan_records
│   ├── operator_service.dart Login, logout, employee ID, JWT token
│   └── backend_config.dart   Server URL (editable in login screen)
├── models/
│   └── scan_record.dart      ScanRecord, SyncStatus, DocumentType
└── widgets/
    └── scan_tile.dart        Scan list item + status timeline (Scanned→Synced→Reviewed→Approved/Rejected)
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
  "extracted_fields": { "hs_code": "...", "invoice_value": "...", ... },
  "flagged_fields": ["missing:hs_code"],
  "ceisa_ready": true
}
```

---

## Risk Scoring Logic

1. **Baseline rules** — missing critical fields (+20 each), low OCR confidence (+15), missing HS code (+10), high value without container (+15), missing importer (+10)
2. **HS code category** — known high-scrutiny prefixes add +10
3. **Watchlist hits** — importer or exporter on watchlist adds +25 per hit
4. **Manager-configured DB rules** — any active `risk_rules` rows applied (field/condition/value/boost)
5. Score capped at 100. Badge: green < 30, yellow 30–70, red > 70.

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
- The XGBoost model does not need real training data until August. Keep the rule-based scorer.
- Do not re-add `google_mlkit_text_recognition` to `pubspec.yaml`.

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

## Seeded Data

**Operators** (seeded on first backend start):
- CDP-001 / Ahmad Fauzi / PIN: 1234
- CDP-002 / Budi Santoso / PIN: 5678
- CDP-003 / Citra Dewi / PIN: 9012

**HS Code Reference** (10 codes seeded):
- Electronics (8471, 8517, 8542) — not restricted
- Weapons (9301, 9302) — restricted, require Ministry of Defense permit
- Chemicals (2710, 2711) — restricted, require energy ministry approval
- Textiles, Food & Beverage — not restricted

---

## Remaining Work (Phase 2 — August 2026)

1. **Real CEISA H2H Integration** — after company visit July 27–31 to get credentials
   - Replace `backend/app/core/ceisa_gateway.py` mock with real HTTP calls
   - Add `CEISA_API_URL`, `CEISA_CLIENT_ID`, `CEISA_SECRET` to `.env`

2. **XGBoost Risk Scorer** — after collecting real rejection data from company visit
   - Training script: `backend/scripts/train_risk_model.py`
   - Model file: `backend/models/risk_model.xgb`
   - Replace rule-based scorer in `backend/app/services/risk_scorer.py`

3. **FCM Service Account** — manual step (no code needed)
   - Firebase console → Project Settings → Service Accounts → Generate new private key
   - Save JSON and set `FCM_SERVICE_ACCOUNT_JSON=/path/to/file.json` in `.env`
