from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.declaration import (
    ConfidenceLevel, Declaration, DeclarationField, ReviewStatus, RiskLevel,
)
from app.schemas.declaration import (
    DeclarationOut, DeclarationUpdate, ExtractedFields,
    FieldBbox, FieldValidationResult, ReviewRequest,
)
from app.services.audit_service import log as audit_log

router = APIRouter(prefix="/declarations", tags=["declarations"])


@router.get("", response_model=list[DeclarationOut])
def list_declarations(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Declaration)
        .order_by(Declaration.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    results = []
    for row in rows:
        fields = {f.field_name: f.field_value for f in row.fields}
        out = DeclarationOut(
            id=row.id,
            scan_id=row.scan_id,
            document_type=row.document_type,
            operator_id=row.operator_id,
            scanned_at=row.scanned_at,
            synced_at=row.synced_at,
            confidence_badge=row.confidence_badge,
            risk_score=row.risk_score,
            risk_badge=row.risk_badge,
            extracted_fields=ExtractedFields(**fields),
            flagged_fields=row.flagged_fields or [],
            ceisa_ready=row.ceisa_ready,
            review_status=row.review_status or ReviewStatus.pending,
            review_note=row.review_note,
            reviewed_by=row.reviewed_by,
            reviewed_at=row.reviewed_at,
            created_at=row.created_at,
        )
        results.append(out)
    return results


@router.get("/{declaration_id}/image")
def get_declaration_image(declaration_id: UUID, db: Session = Depends(get_db)):
    declaration = db.query(Declaration).filter(Declaration.id == declaration_id).first()
    if not declaration:
        raise HTTPException(status_code=404, detail="Declaration not found")
    if not declaration.image_data:
        raise HTTPException(status_code=404, detail="No image stored for this declaration")

    validation_results = _build_validation_out(declaration.fields)

    return {
        "image_data":         declaration.image_data,
        "document_type":      declaration.document_type,
        "image_width":        declaration.image_width,
        "image_height":       declaration.image_height,
        "validation_results": [r.model_dump() for r in validation_results],
    }


@router.patch("/{declaration_id}/field")
def update_field(
    declaration_id: UUID,
    body: DeclarationUpdate,
    db: Session = Depends(get_db),
):
    declaration = db.query(Declaration).filter(Declaration.id == declaration_id).first()
    if not declaration:
        raise HTTPException(status_code=404, detail="Declaration not found")

    field = (
        db.query(DeclarationField)
        .filter(
            DeclarationField.declaration_id == declaration_id,
            DeclarationField.field_name == body.field_name,
        )
        .first()
    )

    if field:
        field.field_value = body.field_value
        field.is_edited = True
        field.edit_source = body.reviewed_by or "web_dashboard"
    else:
        db.add(DeclarationField(
            declaration_id=declaration_id,
            field_name=body.field_name,
            field_value=body.field_value,
            is_edited=True,
            edit_source=body.reviewed_by or "web_dashboard",
        ))

    if body.reviewed_by:
        from datetime import datetime
        declaration.reviewed_by = body.reviewed_by
        declaration.reviewed_at = datetime.utcnow()

    db.commit()
    return {"status": "updated"}


@router.patch("/{declaration_id}/review")
async def review_declaration(
    declaration_id: UUID,
    body: ReviewRequest,
    db: Session = Depends(get_db),
):
    import asyncio
    from datetime import datetime
    from app.config import settings
    from app.services.fcm import send_review_result

    declaration = db.query(Declaration).filter(Declaration.id == declaration_id).first()
    if not declaration:
        raise HTTPException(status_code=404, detail="Declaration not found")

    prev_status = str(declaration.review_status)
    declaration.review_status = body.status
    declaration.review_note = body.note
    declaration.reviewed_by = body.reviewed_by
    declaration.reviewed_at = datetime.utcnow()
    audit_log(db, f"declaration.{body.status.value}", "declaration", str(declaration_id),
              performed_by=body.reviewed_by or "manager",
              detail={"note": body.note, "previous_status": prev_status.replace("ReviewStatus.", "")})
    db.commit()

    if body.status in ("approved", "rejected") and declaration.fcm_token:
        asyncio.create_task(send_review_result(
            fcm_token=declaration.fcm_token,
            status=body.status,
            note=body.note or "",
            project_id=settings.fcm_project_id,
            service_account_json=settings.fcm_service_account_json,
        ))

    return {"status": body.status}


@router.post("/{declaration_id}/reprocess")
def reprocess_declaration(declaration_id: UUID, db: Session = Depends(get_db)):
    from app.services.extractor import extract_fields, find_field_bboxes
    from app.services.ocr import compute_confidence, run_tesseract, run_tesseract_with_boxes
    from app.services.preprocessing import decode_image, decode_pdf_pages, extract_pdf_text_direct, is_pdf, preprocess
    from app.services.risk_scorer import score as compute_risk
    from app.services.validator import validate_fields, validation_risk_boost

    declaration = db.query(Declaration).filter(Declaration.id == declaration_id).first()
    if not declaration:
        raise HTTPException(status_code=404, detail="Declaration not found")
    if not declaration.image_data:
        raise HTTPException(status_code=400, detail="No image stored — cannot reprocess")

    word_data: list[dict] = []
    img_w = declaration.image_width
    img_h = declaration.image_height

    if is_pdf(declaration.image_data):
        direct_text = extract_pdf_text_direct(declaration.image_data)
        if direct_text:
            tesseract_text = direct_text
        else:
            images = decode_pdf_pages(declaration.image_data)
            if images:
                tesseract_text, word_data, img_w, img_h = run_tesseract_with_boxes(images[0])
                for img in images[1:]:
                    tesseract_text += "\n" + run_tesseract(preprocess(img))
            else:
                tesseract_text = ""
    else:
        raw_image = decode_image(declaration.image_data)
        tesseract_text, word_data, img_w, img_h = run_tesseract_with_boxes(raw_image)

    _, confidence_badge = compute_confidence("", tesseract_text)

    from app.api.sync import _load_field_defs
    field_defs = _load_field_defs(db, declaration.document_type.value)

    extraction = extract_fields(tesseract_text, field_defs)
    bboxes     = find_field_bboxes(word_data, extraction)
    v_results  = validate_fields(extraction, field_defs, db=db, bboxes=bboxes)
    extra_risk = validation_risk_boost(v_results)

    risk_score, risk_badge, flagged, _ = compute_risk(
        extraction, confidence_badge, field_defs, db=db,
        document_type=declaration.document_type.value,
    )
    risk_score = min(100, risk_score + extra_risk)
    risk_badge = "green" if risk_score < 30 else "yellow" if risk_score < 70 else "red"

    declaration.tesseract_text = tesseract_text
    declaration.confidence_badge = ConfidenceLevel(confidence_badge)
    declaration.risk_score = risk_score
    declaration.risk_badge = RiskLevel(risk_badge)
    declaration.flagged_fields = flagged
    declaration.ceisa_ready = confidence_badge == "high" and risk_score < 30
    declaration.image_width = img_w
    declaration.image_height = img_h

    db.query(DeclarationField).filter(DeclarationField.declaration_id == declaration_id).delete()
    field_dict = extraction.to_dict()
    vr_map = {r["field_name"]: r for r in v_results}
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

    audit_log(db, "declaration.reprocessed", "declaration", str(declaration_id),
              performed_by="manager",
              detail={"new_risk_score": risk_score, "new_confidence": confidence_badge})
    db.commit()
    return {"status": "reprocessed", "risk_score": risk_score, "confidence_badge": confidence_badge}


def _build_validation_out(fields) -> list[FieldValidationResult]:
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
