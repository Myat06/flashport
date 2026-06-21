# FlashPort

**Snap. Extract. Declare.**

An AI-powered mobile solution for automated customs declaration — built for Cikarang Dry Port.

> AI Open Innovation Challenge 2026 — Case 1: Creating Customs Declaration with OCR
> Team: Teknik Logistik | President University

---

## What It Does

FlashPort eliminates manual customs declaration preparation for Indonesian importers and exporters. A field operator photographs a trade document (Bill of Lading, Commercial Invoice, Packing List) on a Flutter mobile app — even with zero internet. The system extracts all required CEISA fields using a two-stage OCR pipeline, scores the declaration for rejection risk, and submits it automatically when connectivity is available.

**Before FlashPort:** 2–4 hours, manual data entry, high CEISA rejection rate.
**After FlashPort:** under 3 minutes, AI-extracted, pre-submission risk scored.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  MOBILE (Flutter)       BACKEND (FastAPI)    WEB (React)    │
│                                                             │
│  📷 Camera Capture  →   OpenCV Preprocess  →  Live Board   │
│  ML Kit OCR         →   Tesseract OCR      →  Risk Badges  │
│  Offline SQLite     →   Regex Extractor    →  Edit + Submit │
│  Auto-sync          →   XGBoost Scorer     →  CEISA Gate   │
└─────────────────────────────────────────────────────────────┘
```

### Three-Layer Pipeline

| Layer | Tech | Role |
|---|---|---|
| Mobile | Flutter + Google ML Kit | Offline capture, instant OCR preview, operator verification |
| Backend | FastAPI + Tesseract + OpenCV + XGBoost | Server-side OCR truth, regex extraction, risk scoring |
| Web | React + Tailwind CSS | Manager dashboard, live feed, field editing, CEISA submission |
| Database | PostgreSQL | Declaration storage with confidence + risk badges |
| Gateway | Mock CEISA server (FastAPI) | Jalur Hijau/Kuning/Merah simulation |

### How It Works

1. **Operator scans** a trade document with the Flutter camera — completely offline
2. **ML Kit OCR** runs on-device (<100ms), shows instant text preview for quality check
3. **Operator confirms** legibility; app saves `customs_data.json` to SQLite (`Pending Sync`)
4. **On network restore**, background worker auto-syncs compressed image + ML Kit JSON to backend
5. **Backend runs Tesseract** as source-of-truth OCR; compares with ML Kit output → confidence score
6. **Regex engine** extracts HS Code, Invoice Value, Container ID, Importer/Exporter fields
7. **XGBoost scorer** generates 0–100% risk score based on historical CEISA patterns
8. **Web dashboard** receives the record with badges — manager reviews, edits if needed, submits
9. **Mock CEISA gateway** returns Jalur response; Flutter app gets push notification

---

## Project Structure

```
flashport/
├── mobile/          # Flutter app (iOS + Android)
├── backend/         # FastAPI server
├── web/             # React admin dashboard
├── docker/          # PostgreSQL init, nginx config
├── docker-compose.yml
├── README.md
└── CLAUDE.md
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

- Docker & Docker Compose
- Flutter 3.x
- Node.js 18+
- Python 3.11+

### Run the full stack

```bash
# 1. Start backend + database + web
docker-compose up --build

# 2. Run Flutter mobile app
cd mobile
flutter pub get
flutter run
```

Services:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Web Dashboard: http://localhost:3000

### Backend only (local dev)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Web only (local dev)

```bash
cd web
npm install
npm run dev
```

---

## Document Types Supported

| Document | Key Fields | ML Kit Accuracy |
|---|---|---|
| Commercial Invoice | HS Code, Total Value, Invoice No., Importer | Excellent |
| Packing List | Net Weight, Gross Weight, Carton Count | Good |
| Bill of Lading | Container ID, Vessel Name, Port of Origin | Acceptable |

---

## CEISA Jalur Response Guide

| Channel | Condition | Container Action |
|---|---|---|
| Jalur Hijau | Data verified, no anomalies | Immediate release |
| Jalur Kuning | Incomplete fields | Held — manual document upload |
| Jalur Merah | High risk or anomaly | Physical inspection |

---

## Competition Timeline

| Date | Milestone |
|---|---|
| 30 June 2026 | Video submission — working demo of full pipeline |
| 31 August 2026 | Final submission — live CEISA integration, trained Risk Scorer |

---

## Development Roadmap

### Phase 1 — Demo Ready (by 30 June 2026)

| # | Feature | Status |
|---|---|---|
| 1 | Flutter mobile app — offline camera scan + SQLite queue | ✅ Done |
| 2 | FastAPI backend — Tesseract OCR + OpenCV preprocessing | ✅ Done |
| 3 | Regex field extractor (HS Code, Invoice Value, Container ID, etc.) | ✅ Done |
| 4 | Rule-based risk scorer → Jalur Hijau / Kuning / Merah | ✅ Done |
| 5 | Mock CEISA H2H gateway with realistic JSON response | ✅ Done |
| 6 | React web dashboard — live WebSocket feed + field editor | ✅ Done |
| 7 | iOS 26 simulator build fix (arm64 EXCLUDED_ARCHS override) | ✅ Done |
| 8 | OCR confidence scoring fix (Tesseract-only path returns High) | ✅ Done |
| 9 | PDF document upload — mobile picks PDF, backend converts via pdf2image | ✅ Done |
| 10 | Dashboard view — Jalur distribution, confidence breakdown, CEISA readiness | ✅ Done |
| 11 | Analysis view — risk histogram, flagged fields, extraction quality | ✅ Done |
| 12 | Operator identity — name stored in SharedPreferences, shown in dashboard | ✅ Done |
| 13 | API key authentication on all backend routes | 🔲 Next |
| 14 | Multi-page PDF OCR (concatenate all pages) | 🔲 Next |
| 15 | Firebase push notifications (GoogleService-Info.plist setup) | 🔲 Next |

### Phase 2 — Full Prototype (by 31 August 2026)

| # | Feature | Status |
|---|---|---|
| 16 | Real CEISA H2H API integration (credentials from company visit July 27–31) | 🔲 After visit |
| 17 | XGBoost risk scorer trained on real CEISA rejection data | 🔲 After visit |
| 18 | ML Kit on-device OCR (restore when Google ships arm64 simulator slice) | 🔲 Blocked on Google |
| 19 | YOLO v8 document region detector (optional enhancement) | 🔲 Stretch goal |

---

## Tech Stack (100% Free & Open Source)

- Flutter / Dart
- Google ML Kit Text Recognition v2
- Python / FastAPI
- Tesseract OCR (eng+ind)
- OpenCV
- XGBoost
- PostgreSQL
- React + Tailwind CSS
- Docker / Docker Compose
