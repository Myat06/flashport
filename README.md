# FlashPort

**Snap. Extract. Declare.**

An AI-powered customs declaration automation platform built for Cikarang Dry Port.

> AI Open Innovation Challenge 2026 — Case 1: Creating Customs Declaration with OCR
> Team: Teknik Logistik | President University

---

## What It Does

FlashPort eliminates manual customs declaration preparation for Indonesian importers and exporters. A field operator photographs a trade document (Bill of Lading, Commercial Invoice, Packing List) on a Flutter mobile app — even with zero internet. The backend extracts all required CEISA fields using Tesseract OCR, scores the declaration for rejection risk, and the manager reviews and submits through a professional web dashboard.

**Before FlashPort:** 2–4 hours, manual data entry, high CEISA rejection rate.
**After FlashPort:** Under 3 minutes, AI-extracted, pre-submission risk scored.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  MOBILE (Flutter)        BACKEND (FastAPI)      WEB (React)      │
│                                                                  │
│  📷 Camera / File    →   OpenCV Preprocess   →  Admin Dashboard  │
│  Offline SQLite      →   Tesseract OCR       →  Approve/Reject   │
│  Auto-sync           →   Regex Extractor     →  CEISA Submit     │
│  FCM Notifications   →   Risk Scorer         →  Audit Trail      │
│                      →   Watchlist Check     →  SLA Monitoring   │
│                      →   PostgreSQL          →  Export / Reports  │
└──────────────────────────────────────────────────────────────────┘
```

### Three-Layer Pipeline

| Layer | Tech | Role |
|---|---|---|
| Mobile | Flutter + SQLite | Offline document capture, auto-sync, status timeline |
| Backend | FastAPI + Tesseract + OpenCV | Server-side OCR, extraction, risk scoring, all business logic |
| Web | React + Tailwind CSS | Pro admin dashboard — review, approve/reject, CEISA submit, reports |
| Database | PostgreSQL | All data including stored document images |
| Gateway | Mock CEISA (FastAPI) | Green/Yellow/Red lane simulation |

### How It Works

1. **Operator scans** a trade document with the Flutter camera or attaches a file — completely offline
2. **App saves** to local SQLite as `Pending` — shows in scan history immediately
3. **On network restore**, auto-sync sends compressed image to backend
4. **Backend runs Tesseract** OCR; OpenCV preprocesses (grayscale, threshold, deskew)
5. **Regex engine** extracts HS Code, Invoice Value, Container ID, Importer/Exporter, etc.
6. **Risk scorer** generates 0–100% risk score, checks against watchlist and custom rules
7. **Web dashboard** receives the record live via WebSocket — manager reviews, approves or rejects
8. **On approve/reject**, FCM push notification sent to the operator's mobile device
9. **Manager submits** approved declarations to the mock CEISA gateway — Green/Yellow/Red lane response

---

## Project Structure

```
flashport/
├── mobile/                 Flutter app (iOS + Android)
│   ├── lib/
│   │   ├── screens/        camera, preview, result, home, login
│   │   ├── services/       sync, database, operator, backend_config
│   │   ├── models/         scan_record
│   │   └── widgets/        scan_tile (status timeline)
│   └── pubspec.yaml
│
├── backend/                FastAPI Python server
│   ├── app/
│   │   ├── api/            38 routes across 12 routers
│   │   ├── models/         7 SQLAlchemy models
│   │   ├── services/       OCR, extractor, risk scorer, FCM, audit
│   │   └── core/           CEISA gateway simulation
│   └── requirements.txt
│
├── web/                    React 18 + Tailwind CSS admin dashboard
│   └── src/
│       ├── components/     15 components (sidebar, table, detail panel, all views)
│       └── hooks/          useAuth, useDeclarations, useAPI, useCeisaSubmissions
│
├── docker/
│   └── postgres/init.sql   Full schema
├── CLAUDE.md               Developer context for AI assistants
├── SYSTEM_BREAKDOWN.md     Technical implementation plan
└── README.md               This file
```

---

## Team

| Name | Role |
|---|---|
| Bayu Pratama Putra Gunawan | Project Manager & AI Engineer |
| Myat Min Thu | Mobile Developer (Flutter) |
| Matthew Nazim | Backend & API Integration |
| Jonathan Gifford | UI/UX Designer |

---

## Quick Start

### Prerequisites

- PostgreSQL 15 (local install via Homebrew or pgAdmin)
- Flutter 3.x
- Node.js 18+
- Python 3.11+
- Tesseract OCR (`brew install tesseract`)

### Database Setup (first time only)

```bash
# Create user and database
psql postgres -c "CREATE USER flashport WITH PASSWORD 'flashport';"
psql postgres -c "CREATE DATABASE flashport OWNER flashport;"

# Run schema
psql -U flashport -d flashport -f docker/postgres/init.sql
```

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL, TESSERACT_CMD as needed
uvicorn app.main:app --reload --port 8000
```

### Web Dashboard

```bash
cd web
npm install
npm run dev
# Opens at http://localhost:3000
```

**Manager login:** `manager` / `flashport2026`

### Mobile

```bash
cd mobile
flutter pub get
flutter run
```

Services:
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Web Dashboard: `http://localhost:3000`

---

## Document Types Supported

| Document | Key Fields Extracted |
|---|---|
| Commercial Invoice | HS Code, Invoice Value, Invoice No., Importer, Exporter |
| Packing List | Net Weight, Gross Weight, Carton Count |
| Bill of Lading | Container ID, Vessel Name, Port of Origin |

---

## CEISA Lane Response Guide

| Lane | Condition | Action |
|---|---|---|
| Green Lane | Data verified, risk < 30% | Immediate release |
| Yellow Lane | Incomplete fields, risk 30–70% | Held — document verification |
| Red Lane | High risk > 70% or anomaly | Physical inspection |

---

## API Overview

| Group | Endpoints | Description |
|---|---|---|
| Auth | `POST /auth/login` | Manager JWT login |
| Sync | `POST /sync` | Mobile document sync |
| Declarations | `GET/PATCH /declarations` | List, review, reprocess |
| CEISA | `POST /ceisa/submit`, `/batch-submit` | Single and batch submission |
| Operators | `GET/POST/PATCH/DELETE /operators` | Field operator management |
| Watchlist | `GET/POST/DELETE /watchlist` | Flag risky entities |
| Risk Rules | `GET/POST/PATCH/DELETE /risk-rules` | Custom scoring rules |
| HS Codes | `GET /hs-codes/validate/{code}` | HS code validation |
| SLA | `GET /sla` | Processing time metrics |
| Audit | `GET /audit` | Full action history |
| Export | `GET /export/declarations.csv` | CSV export |

Full interactive docs: `http://localhost:8000/docs`

---

## Development Roadmap

### Phase 1 — Core Platform ✅ Complete

| Feature | Status |
|---|---|
| Flutter mobile — offline capture, SQLite queue, auto-sync | ✅ |
| FastAPI backend — Tesseract OCR + OpenCV preprocessing | ✅ |
| Regex field extractor (HS Code, Invoice Value, Container ID, etc.) | ✅ |
| Rule-based + configurable risk scorer | ✅ |
| Mock CEISA H2H gateway (Green/Yellow/Red lane) | ✅ |
| Professional React admin dashboard (sidebar, table, detail panel) | ✅ |
| Approve / Reject workflow with manager notes | ✅ |
| Operator management (add, deactivate, reset PIN) | ✅ |
| Watchlist — auto-flag risky importers/exporters/HS codes | ✅ |
| Custom risk rules — configurable field/condition/boost | ✅ |
| HS Code reference database + validator | ✅ |
| SLA Dashboard — overdue alerts, daily throughput | ✅ |
| Full audit trail — every action logged | ✅ |
| CSV export with filters | ✅ |
| Batch CEISA submission | ✅ |
| Re-run OCR on stored document | ✅ |
| PDF document upload + multi-page OCR | ✅ |
| Document image stored in PostgreSQL | ✅ |
| Firebase push notifications (approve/reject + CEISA result) | ✅ (needs FCM JSON) |
| Mobile scan history with status timeline | ✅ |

### Phase 2 — Live Integration (by 31 August 2026)

| Feature | Status |
|---|---|
| Real CEISA H2H API integration (credentials from company visit July 27–31) | 🔲 After visit |
| XGBoost risk scorer trained on real CEISA rejection data | 🔲 After visit |
| Firebase FCM service account JSON configured | 🔲 Manual step |

---

## Tech Stack (100% Free & Open Source)

| Component | Technology |
|---|---|
| Mobile | Flutter 3.x + Dart |
| Mobile OCR | Tesseract (backend only — no on-device OCR) |
| Backend | Python 3.11 + FastAPI |
| OCR Engine | Tesseract `eng+ind` |
| Preprocessing | OpenCV + pdf2image + poppler |
| Field Extraction | Python Regex |
| Risk Scoring | Rule-based scorer (XGBoost in Phase 2) |
| Database | PostgreSQL 15 |
| Web Frontend | React 18 + Tailwind CSS 3 |
| Push Notifications | Firebase Cloud Messaging (FCM HTTP v1) |
| Auth | JWT (python-jose) + API Key |
