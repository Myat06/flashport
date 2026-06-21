from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.declaration import Declaration, DeclarationField
from app.schemas.declaration import DeclarationOut, DeclarationUpdate, ExtractedFields

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
            extracted_fields=ExtractedFields(**{k: fields.get(k) for k in ExtractedFields.model_fields}),
            flagged_fields=row.flagged_fields or [],
            ceisa_ready=row.ceisa_ready,
            created_at=row.created_at,
        )
        results.append(out)
    return results


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
