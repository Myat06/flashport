import time

from fastapi import APIRouter, Depends
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
from app.schemas.declaration import ExtractedFields, SyncPayload, SyncResponse
from app.services.audit_service import log as audit_log
from app.services.extractor import extract_fields
from app.services.ocr import compute_confidence, run_tesseract
from app.services.preprocessing import decode_image, decode_pdf_pages, extract_pdf_text_direct, is_pdf, preprocess
from app.services.risk_scorer import score as compute_risk

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", response_model=SyncResponse)
async def sync_document(payload: SyncPayload, db: Session = Depends(get_db)):
    # Idempotent: return existing record if scan_id already processed
    existing = db.query(Declaration).filter(Declaration.scan_id == payload.scan_id).first()
    if existing:
        fields = {f.field_name: f.field_value for f in existing.fields}
        return SyncResponse(
            declaration_id=existing.id,
            confidence_badge=existing.confidence_badge,
            risk_score=existing.risk_score or 0,
            risk_badge=existing.risk_badge,
            extracted_fields=ExtractedFields(**{k: fields.get(k) for k in ExtractedFields.model_fields}),
            flagged_fields=existing.flagged_fields or [],
            ceisa_ready=existing.ceisa_ready,
        )

    start = time.time()

    if is_pdf(payload.image_b64):
        # Try direct text extraction first (works on digital PDFs — much better than OCR on tables)
        direct_text = extract_pdf_text_direct(payload.image_b64)
        if direct_text:
            tesseract_text = direct_text
        else:
            # Fall back to Tesseract OCR (for scanned/image-based PDFs)
            images = decode_pdf_pages(payload.image_b64)
            tesseract_text = "\n".join(run_tesseract(preprocess(img)) for img in images)
    else:
        tesseract_text = run_tesseract(preprocess(decode_image(payload.image_b64)))

    confidence_score, confidence_badge = compute_confidence(payload.ml_kit_text, tesseract_text)
    extraction = extract_fields(tesseract_text)

    # Check watchlist
    from app.models.watchlist import WatchlistEntry
    watchlist_hits = []
    for etype, val in [("importer", extraction.importer), ("exporter", extraction.exporter)]:
        if val:
            hit = db.query(WatchlistEntry).filter(
                WatchlistEntry.entity_type == etype,
                WatchlistEntry.value.ilike(val.strip()),
                WatchlistEntry.is_active == True,  # noqa: E712
            ).first()
            if hit:
                watchlist_hits.append({"entity_type": etype, "value": val, "reason": hit.reason})

    risk_score, risk_badge, flagged, shap_values = compute_risk(
        extraction, confidence_badge, db=db, watchlist_hits=watchlist_hits
    )
    ceisa_ready = confidence_badge == "high" and risk_score < 30

    declaration = Declaration(
        scan_id=payload.scan_id,
        document_type=payload.document_type,
        operator_id=payload.operator_id,
        device_id=payload.device_id,
        fcm_token=payload.fcm_token,
        scanned_at=payload.scanned_at,
        image_data=payload.image_b64,
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

    field_dict = extraction.to_dict()
    for name, value in field_dict.items():
        if value:
            db.add(DeclarationField(declaration_id=declaration.id, field_name=name, field_value=value))

    elapsed_ms = int((time.time() - start) * 1000)
    db.add(SyncLog(
        scan_id=payload.scan_id,
        device_id=payload.device_id,
        image_size_bytes=len(payload.image_b64) * 3 // 4,
        ml_kit_char_count=len(payload.ml_kit_text),
        sync_duration_ms=elapsed_ms,
        status="success",
    ))

    audit_log(db, "declaration.created", "declaration", str(declaration.id),
              performed_by=payload.operator_id or "mobile",
              detail={"risk_score": risk_score, "risk_badge": risk_badge,
                      "watchlist_hits": len(watchlist_hits), "document_type": payload.document_type})
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
        shap_values=shap_values,
        extraction_method=extraction.extraction_method,
    )

    await broadcast({"event": "new_declaration", "data": response.model_dump(mode="json")})
    return response
