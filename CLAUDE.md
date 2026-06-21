# FlashPort — CLAUDE.md

This file gives Claude Code the full context needed to work on FlashPort without rederiving it from scratch.

## Project Identity

FlashPort is an AI-powered customs declaration automation platform built for the AI Open Innovation Challenge 2026 (Case 1 — Cikarang Dry Port). It is a monorepo with three independent deployable services.

**Hard deadline:** 30 June 2026 — video demo submission.
**Final deadline:** 31 August 2026 — full working prototype.

---

## Monorepo Layout

```
flashport/
├── mobile/       Flutter app — offline-first field scanning
├── backend/      FastAPI Python server — OCR, extraction, scoring
├── web/          React dashboard — manager review and CEISA submission
├── docker/       postgres init.sql, nginx config
└── docker-compose.yml
```

---

## Architecture Rules

### Mobile (Flutter)
- Offline-first. The app must work with zero network connectivity.
- ML Kit OCR is for **operator preview only** — not the data source of truth.
- Data saved locally as `customs_data.json` in SQLite/Hive with `status: pending_sync`.
- Images compressed to ~200–400KB before upload.
- Background sync fires the moment `connectivity_plus` detects network.
- Push notifications via Firebase Cloud Messaging (FCM).

### Backend (FastAPI)
- Tesseract OCR (`eng+ind`) is the **source of truth** for all field extraction.
- Parallel comparison: ML Kit text vs Tesseract text → confidence score.
- Three confidence levels: High (auto-process), Medium (flag for review), Low (hold).
- Regex extraction gates:
  - HS Code: 8-digit `XXXX.XX.XX`
  - Invoice Value: currency symbol + numeric
  - Container ID: `ABCD1234567`
  - Importer/Exporter: registered entity name
- XGBoost risk scorer: 0–100% (mock random until August training sprint).
- All records persisted to PostgreSQL with `confidence_badge` + `risk_badge`.
- WebSocket endpoint pushes new records to the React dashboard in real time.

### Web Dashboard (React + Tailwind)
- Split-screen: field data left, AI analysis right.
- Records arrive live via WebSocket with two badges per record.
- Manager can edit any field inline before submission.
- Submit button → mock CEISA gateway → Jalur response displayed.
- Risk badge colours: green < 30%, yellow 30–70%, red > 70%.

### Mock CEISA Gateway (FastAPI `/ceisa/submit`)
- No real CEISA credentials in Phase 1. Use the mock until August.
- Jalur logic: risk < 30 → Hijau, 30–70 → Kuning, > 70 → Merah.
- Returns realistic JSON matching the real CEISA H2H API response shape.

---

## Stack Summary

| Layer | Tech | Notes |
|---|---|---|
| Mobile | Flutter 3.x + Dart | `mobile/` |
| Mobile OCR | **STUBBED** — Google ML Kit v2 | Removed: no arm64 iOS 26 simulator slice. Returns `''`. Restore when Google ships XCFramework. |
| Backend | Python 3.11 + FastAPI | `backend/` |
| Backend OCR | Tesseract `eng+ind` | Source of truth. Must install system binary. |
| Preprocessing | OpenCV (Python) | grayscale → threshold → deskew. PDF → image via `pdf2image` + `poppler-utils`. |
| Field Extraction | Python Regex | Strict patterns per field type |
| Risk Scoring | Rule-based scorer | Mock only. Replace with XGBoost after August company visit data. |
| Database | PostgreSQL 15 | Via Docker |
| Web | React 18 + Tailwind CSS 3 | `web/` — Live Feed, Dashboard, Analysis views |
| Infra | Docker Compose | Local dev + CI |

---

## Environment Variables

Backend `.env` (copy from `.env.example`):
```
DATABASE_URL=postgresql://flashport:flashport@localhost:5432/flashport
TESSERACT_CMD=/usr/bin/tesseract
FCM_SERVER_KEY=
SECRET_KEY=changeme
```

---

## Key Commands

```bash
# Full stack
docker-compose up --build

# Backend only
cd backend && uvicorn app.main:app --reload

# Web only
cd web && npm run dev

# Flutter
cd mobile && flutter run

# Run backend tests
cd backend && pytest

# Lint backend
cd backend && ruff check .
```

---

## Data Contract — `customs_data.json`

This is the payload mobile sends to the backend on sync:

```json
{
  "scan_id": "uuid-v4",
  "scanned_at": "2026-06-18T10:00:00Z",
  "document_type": "commercial_invoice | bill_of_lading | packing_list",
  "operator_id": "string",
  "ml_kit_text": "raw OCR text from ML Kit",
  "image_b64": "base64-encoded compressed image ~200-400KB",
  "device_id": "string"
}
```

Backend response after processing:

```json
{
  "declaration_id": "uuid-v4",
  "confidence_badge": "high | medium | low",
  "risk_score": 42,
  "risk_badge": "green | yellow | red",
  "extracted_fields": {
    "hs_code": "8471.30.00",
    "invoice_value": "USD 12,500.00",
    "container_id": "TCKU1234567",
    "importer": "PT Maju Jaya",
    "exporter": "Samsung Electronics Co.",
    "net_weight": "450 KG",
    "gross_weight": "520 KG",
    "vessel_name": "MV Pacific Star",
    "port_of_origin": "Busan, Korea"
  },
  "flagged_fields": [],
  "ceisa_ready": true
}
```

---

## PostgreSQL Schema (Key Tables)

- `declarations` — main record table, one row per document scan
- `declaration_fields` — extracted key-value pairs linked to declaration
- `sync_logs` — mobile sync events, timestamps, payload sizes
- `ceisa_submissions` — submission attempts and Jalur responses

---

## What NOT to Do

- Do not use YOLO v8 or Gemini Vision API in the current build — those are in the proposal but not in the System Breakdown which is the authoritative implementation plan.
- Do not call any paid external APIs. Stack is 100% free/open-source.
- Do not hardcode credentials. Use `.env` files.
- Do not re-add `google_mlkit_text_recognition` to `pubspec.yaml` until Google ships a proper XCFramework with arm64 simulator slices. The current stub (`lib/services/ocr_service.dart` returns `''`) is intentional — `compute_confidence()` handles this by returning `(0.85, "high")` when `ml_kit_text` is empty.
- The XGBoost model does not need real training data until August. Keep the rule-based `risk_scorer.py` mock until then.

---

## Competition Context

- **Challenge:** AI Open Innovation Challenge 2026, Case 1 — Cikarang Dry Port
- **Team:** Teknik Logistik, President University
- **Phase 1 goal:** Demo video showing scan → OCR → risk score → mock CEISA Jalur response (deadline: 30 June 2026)
- **Phase 2 goal:** Live CEISA H2H integration, XGBoost risk scorer trained on real data from company visit (July 27–31 2026), final prototype (deadline: 31 August 2026)

---

## Credentials & Secrets

| Secret | Value | Where |
|---|---|---|
| Web dashboard login | `manager` / `flashport2026` | `backend/.env` — `MANAGER_USERNAME` / `MANAGER_PASSWORD` |
| Backend API key (mobile auth) | `changeme` (change in prod) | `backend/.env` — `API_KEY` |
| JWT secret | `changeme` (change in prod) | `backend/.env` — `SECRET_KEY` |
| Firebase Android config | placed | `mobile/android/app/google-services.json` |
| Firebase iOS config | placed | `mobile/ios/Runner/GoogleService-Info.plist` |
| FCM service account JSON | **not yet downloaded** | `backend/.env` — `FCM_SERVICE_ACCOUNT_JSON=/path/to/file.json` |

To change the manager password: edit `MANAGER_PASSWORD=` in `backend/.env`.

---

## Current Implementation Status (as of 2026-06-20)

### ✅ Completed — Phase 1

| Item | Files |
|---|---|
| iOS 26 simulator fix — removed MLKit, EXCLUDED_ARCHS override | `mobile/pubspec.yaml`, `mobile/ios/Podfile`, `mobile/ios/Runner.xcodeproj/project.pbxproj`, `mobile/lib/services/ocr_service.dart` |
| Confidence scoring fix — empty ml_kit_text → (0.85, "high") | `backend/app/services/ocr.py` |
| PDF upload support — mobile picks PDF files, backend converts via pdf2image | `mobile/pubspec.yaml`, `mobile/lib/screens/camera_screen.dart`, `mobile/lib/services/sync_service.dart`, `backend/app/services/preprocessing.py`, `backend/requirements.txt`, `backend/Dockerfile` |
| Multi-page PDF OCR — all pages concatenated, not just page 1 | `backend/app/services/preprocessing.py` (`decode_pdf_pages`, `is_pdf`), `backend/app/api/sync.py` |
| Web dashboard — Live Feed + Dashboard + Analysis + Portal CEISA tabs | `web/src/App.jsx`, `web/src/components/` |
| Portal CEISA tab — government-portal UI, lists all submissions with Jalur badges | `web/src/components/CeisaView.jsx`, `web/src/hooks/useCeisaSubmissions.js`, `backend/app/api/ceisa.py` (`GET /ceisa/submissions`) |
| Manager login — JWT auth, LoginPage, logout button, 8h token expiry | `backend/app/api/auth.py`, `web/src/hooks/useAuth.js`, `web/src/components/LoginPage.jsx` |
| API Key auth — middleware accepts X-API-Key (mobile) OR Bearer JWT (web) | `backend/app/main.py`, `backend/app/config.py` |
| Firebase config files placed — both platforms launch without crash | `mobile/android/app/google-services.json`, `mobile/ios/Runner/GoogleService-Info.plist` |
| Firebase options generated — `DefaultFirebaseOptions.currentPlatform` wired | `mobile/lib/firebase_options.dart`, `mobile/lib/main.dart` |
| FCM push notification — backend sends push to operator after CEISA result | `backend/app/services/fcm.py`, `backend/app/api/ceisa.py`, `mobile/lib/services/sync_service.dart` (sends `fcm_token` on sync) |
| Operator ID — SharedPreferences-backed name, dialog in HomeScreen, sent on sync | `mobile/lib/services/operator_service.dart`, `mobile/lib/screens/home_screen.dart` |
| Android permissions — INTERNET, CAMERA, storage (scoped + legacy), POST_NOTIFICATIONS | `mobile/android/app/src/main/AndroidManifest.xml` |
| Android Firebase Gradle plugin wired — google-services v4.4.2 | `mobile/android/settings.gradle.kts`, `mobile/android/app/build.gradle.kts` |
| Preview screen — shows document type, OCR info, Save & Sync flow | `mobile/lib/screens/preview_screen.dart` |
| Result screen — risk card, confidence badge, CEISA-ready badge, extracted fields, flagged issues | `mobile/lib/screens/result_screen.dart` |

### ⏳ One Manual Step Remaining (to activate FCM)
Download Firebase service account JSON and set path in `.env`:
1. Firebase console → Project Settings → Service Accounts → **Generate new private key**
2. Save file on server
3. Add to `backend/.env`: `FCM_SERVICE_ACCOUNT_JSON=/path/to/flashport-service-account.json`

Without this, backend logs a warning and continues — push notifications are silently skipped, everything else works.

---

## Remaining Work

### Phase 2 — Before 31 August 2026 (final prototype)

#### 1. Real CEISA H2H Integration
After company visit (July 27–31, 2026) to get API credentials:
- Replace `backend/app/core/ceisa_gateway.py` mock with real HTTP calls to CEISA PIB XML/JSON endpoint
- Add credentials to `.env`: `CEISA_API_URL`, `CEISA_CLIENT_ID`, `CEISA_SECRET`
- Handle real error codes and retry logic

#### 2. XGBoost Risk Scorer Training
After collecting real CEISA rejection data from company visit:
- Replace `backend/app/services/risk_scorer.py` rule-based logic with a trained XGBoost model
- Training script goes in `backend/scripts/train_risk_model.py`
- Serialized model → `backend/models/risk_model.xgb`
- `risk_scorer.py` loads model at startup via `xgboost.Booster().load_model()`

#### 3. ML Kit Restoration
When Google ships `google_mlkit_text_recognition` with proper XCFramework (arm64 simulator slice):
- Re-add `google_mlkit_text_recognition: ^0.15.x` to `mobile/pubspec.yaml`
- Restore `mobile/lib/services/ocr_service.dart` with the real `InputImage` + `TextRecognizer` implementation
- Remove the stub. The `compute_confidence()` function will automatically resume Jaccard scoring once `ml_kit_text` is non-empty.
