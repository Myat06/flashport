import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.ws import broadcast
from app.database import get_db
from app.models.declaration import (
    ConfidenceLevel,
    Declaration,
    DeclarationField,
    RiskLevel,
    SyncLog,
)
from app.schemas.declaration import SyncPayload, SyncResponse, ExtractedFields
from app.services.extractor import extract_fields
from app.services.ocr import compute_confidence, run_tesseract
from app.services.preprocessing import decode_image, decode_pdf_pages, is_pdf, preprocess
from app.services.risk_scorer import score as compute_risk

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", response_model=SyncResponse)
async def sync_document(payload: SyncPayload, db: Session = Depends(get_db)):
    start = time.time()

    # Decode + preprocess + OCR (all pages for PDF, single image otherwise)
    if is_pdf(payload.image_b64):
        images = decode_pdf_pages(payload.image_b64)
        tesseract_text = "\n".join(run_tesseract(preprocess(img)) for img in images)
    else:
        tesseract_text = run_tesseract(preprocess(decode_image(payload.image_b64)))

    # Confidence: compare ML Kit vs Tesseract
    confidence_score, confidence_badge = compute_confidence(payload.ml_kit_text, tesseract_text)

    # Field extraction via regex
    extraction = extract_fields(tesseract_text)

    # Risk scoring
    risk_score, risk_badge, flagged = compute_risk(extraction, confidence_badge)

    ceisa_ready = confidence_badge == "high" and risk_score < 30

    # Persist declaration
    declaration = Declaration(
        scan_id=payload.scan_id,
        document_type=payload.document_type,
        operator_id=payload.operator_id,
        device_id=payload.device_id,
        fcm_token=payload.fcm_token,
        scanned_at=payload.scanned_at,
        ml_kit_text=payload.ml_kit_text,
        tesseract_text=tesseract_text,
        confidence_badge=ConfidenceLevel(confidence_badge),
        risk_score=risk_score,
        risk_badge=RiskLevel(risk_badge),
        flagged_fields=flagged,
        ceisa_ready=ceisa_ready,
    )
    db.add(declaration)
    db.flush()

    # Persist extracted fields
    field_dict = extraction.to_dict()
    for name, value in field_dict.items():
        if value:
            db.add(DeclarationField(
                declaration_id=declaration.id,
                field_name=name,
                field_value=value,
            ))

    # Log sync event
    elapsed_ms = int((time.time() - start) * 1000)
    db.add(SyncLog(
        scan_id=payload.scan_id,
        device_id=payload.device_id,
        image_size_bytes=len(payload.image_b64) * 3 // 4,
        ml_kit_char_count=len(payload.ml_kit_text),
        sync_duration_ms=elapsed_ms,
        status="success",
    ))

    db.commit()
    db.refresh(declaration)

    extracted = ExtractedFields(**field_dict)
    response = SyncResponse(
        declaration_id=declaration.id,
        confidence_badge=ConfidenceLevel(confidence_badge),
        risk_score=risk_score,
        risk_badge=RiskLevel(risk_badge),
        extracted_fields=extracted,
        flagged_fields=flagged,
        ceisa_ready=ceisa_ready,
    )

    # Push to web dashboard via WebSocket
    await broadcast({
        "event": "new_declaration",
        "data": response.model_dump(mode="json"),
    })

    return response
