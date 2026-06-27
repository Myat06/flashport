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
from app.schemas.declaration import (
    ExtractedFields,
    FieldBbox,
    FieldValidationResult,
    SyncPayload,
    SyncResponse,
)
from app.services.audit_service import log as audit_log
from app.services.extractor import extract_fields, find_field_bboxes
from app.services.ocr import compute_confidence, run_tesseract, run_tesseract_with_boxes
from app.services.preprocessing import (
    decode_image,
    decode_pdf_pages,
    extract_pdf_text_direct,
    is_pdf,
    preprocess,
)
from app.services.risk_scorer import score as compute_risk
from app.services.validator import validate_fields, validation_risk_boost

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", response_model=SyncResponse)
async def sync_document(payload: SyncPayload, db: Session = Depends(get_db)):
    # Idempotent: return existing record if scan_id already processed
    existing = db.query(Declaration).filter(Declaration.scan_id == payload.scan_id).first()
    if existing:
        fields    = {f.field_name: f.field_value for f in existing.fields}
        v_results = _build_validation_out(existing.fields)
        return SyncResponse(
            declaration_id=existing.id,
            confidence_badge=existing.confidence_badge,
            risk_score=existing.risk_score or 0,
            risk_badge=existing.risk_badge,
            extracted_fields=ExtractedFields(**fields),
            flagged_fields=existing.flagged_fields or [],
            ceisa_ready=existing.ceisa_ready,
            validation_results=v_results,
            image_width=existing.image_width,
            image_height=existing.image_height,
        )

    start = time.time()

    word_data: list[dict] = []
    img_w: int | None = None
    img_h: int | None = None

    if is_pdf(payload.image_b64):
        direct_text = extract_pdf_text_direct(payload.image_b64)
        if direct_text:
            tesseract_text = direct_text
            # No image coords available for native-text PDFs
        else:
            images = decode_pdf_pages(payload.image_b64)
            if images:
                # Bboxes from first page; text from all pages
                tesseract_text, word_data, img_w, img_h = run_tesseract_with_boxes(images[0])
                for img in images[1:]:
                    tesseract_text += "\n" + run_tesseract(preprocess(img))
            else:
                tesseract_text = ""
    else:
        raw_image = decode_image(payload.image_b64)
        tesseract_text, word_data, img_w, img_h = run_tesseract_with_boxes(raw_image)

    confidence_score, confidence_badge = compute_confidence(payload.ml_kit_text, tesseract_text)

    # Load field definitions relevant to this document type
    field_defs = _load_field_defs(db, payload.document_type.value)

    extraction = extract_fields(tesseract_text, field_defs)

    # Bounding boxes for each extracted field
    bboxes = find_field_bboxes(word_data, extraction)

    # Validation
    v_results_raw = validate_fields(extraction, field_defs, db=db, bboxes=bboxes)
    extra_risk    = validation_risk_boost(v_results_raw)

    # Watchlist check (check any field named importer/exporter or with those keywords)
    from app.models.watchlist import WatchlistEntry
    watchlist_hits = []
    for etype in ("importer", "exporter"):
        val = extraction.get(etype)
        if val:
            hit = db.query(WatchlistEntry).filter(
                WatchlistEntry.entity_type == etype,
                WatchlistEntry.value.ilike(val.strip()),
                WatchlistEntry.is_active == True,  # noqa: E712
            ).first()
            if hit:
                watchlist_hits.append({"entity_type": etype, "value": val, "reason": hit.reason})

    risk_score, risk_badge, flagged, shap_values = compute_risk(
        extraction, confidence_badge, field_defs, db=db, watchlist_hits=watchlist_hits,
        document_type=payload.document_type.value,
    )
    risk_score = min(100, risk_score + extra_risk)
    risk_badge = "green" if risk_score < 30 else "yellow" if risk_score < 70 else "red"

    ceisa_ready = confidence_badge == "high" and risk_score < 30

    declaration = Declaration(
        scan_id=payload.scan_id,
        document_type=payload.document_type,
        operator_id=payload.operator_id,
        device_id=payload.device_id,
        fcm_token=payload.fcm_token,
        scanned_at=payload.scanned_at,
        image_data=payload.image_b64,
        image_width=img_w,
        image_height=img_h,
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

    # Store fields with bbox + validation metadata
    field_dict = extraction.to_dict()
    vr_map     = {r["field_name"]: r for r in v_results_raw}
    for name, value in field_dict.items():
        if value is None:
            continue
        vr  = vr_map.get(name, {})
        box = vr.get("bbox")
        db.add(DeclarationField(
            declaration_id=declaration.id,
            field_name=name,
            field_value=value,
            bbox_x=box["x"] if box else None,
            bbox_y=box["y"] if box else None,
            bbox_w=box["w"] if box else None,
            bbox_h=box["h"] if box else None,
            is_valid=vr.get("is_valid"),
            validation_message=vr.get("message"),
            priority=vr.get("priority"),
        ))

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

    v_out     = _v_results_to_schema(v_results_raw)
    extracted = ExtractedFields(**field_dict)
    response  = SyncResponse(
        declaration_id=declaration.id,
        confidence_badge=ConfidenceLevel(confidence_badge),
        risk_score=risk_score,
        risk_badge=RiskLevel(risk_badge),
        extracted_fields=extracted,
        flagged_fields=flagged,
        ceisa_ready=ceisa_ready,
        shap_values=shap_values,
        extraction_method=extraction.extraction_method,
        validation_results=v_out,
        image_width=img_w,
        image_height=img_h,
    )

    await broadcast({"event": "new_declaration", "data": response.model_dump(mode="json")})
    return response


def _load_field_defs(db, doc_type: str = "") -> list[dict]:
    """Load active field definitions relevant to a given document type.

    Fields with applicable_doc_types=NULL apply to every doc type.
    Fields with a value only apply when doc_type appears in that comma-separated list.
    """
    from app.models.field_definition import FieldDefinition
    rows = (
        db.query(FieldDefinition)
        .filter(FieldDefinition.is_active == True)  # noqa: E712
        .order_by(FieldDefinition.sort_order, FieldDefinition.id)
        .all()
    )
    return [
        {
            "field_key":           r.field_key,
            "display_label":       r.display_label,
            "priority":            r.priority,
            "extraction_keywords": r.extraction_keywords or "",
            "risk_weight":         r.risk_weight or 0,
        }
        for r in rows
        if not r.applicable_doc_types                           # NULL → all types
        or (doc_type and doc_type in r.applicable_doc_types.split(","))
    ]


def _build_validation_out(fields) -> list[FieldValidationResult]:
    """Reconstruct validation results from stored DeclarationField rows."""
    results = []
    for f in fields:
        if f.priority is None:
            continue
        bbox = None
        if f.bbox_x is not None:
            bbox = FieldBbox(x=f.bbox_x, y=f.bbox_y, w=f.bbox_w, h=f.bbox_h)
        results.append(FieldValidationResult(
            field_name=f.field_name,
            value=f.field_value,
            is_valid=f.is_valid if f.is_valid is not None else True,
            priority=f.priority,
            message=f.validation_message,
            bbox=bbox,
        ))
    return results


def _v_results_to_schema(raw: list[dict]) -> list[FieldValidationResult]:
    out = []
    for r in raw:
        box = r.get("bbox")
        out.append(FieldValidationResult(
            field_name=r["field_name"],
            value=r.get("value"),
            is_valid=r["is_valid"],
            priority=r["priority"],
            message=r.get("message"),
            bbox=FieldBbox(**box) if box else None,
        ))
    return out
