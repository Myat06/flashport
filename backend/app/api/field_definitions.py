from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.field_definition import FieldDefinition

router = APIRouter(prefix="/field-definitions", tags=["field-definitions"])

VALID_DOC_TYPES = {"commercial_invoice", "bill_of_lading", "packing_list"}


def _validate_doc_types(value: Optional[str]) -> Optional[str]:
    """Validate comma-separated doc type string. Returns None for 'all'."""
    if not value or value.strip() == "":
        return None
    parts = [p.strip() for p in value.split(",") if p.strip()]
    bad = [p for p in parts if p not in VALID_DOC_TYPES]
    if bad:
        raise HTTPException(400, f"Invalid doc types: {bad}. Must be one of {sorted(VALID_DOC_TYPES)}")
    return ",".join(sorted(set(parts)))


class FieldDefOut(BaseModel):
    id: int
    field_key: str
    display_label: str
    priority: str
    extraction_keywords: Optional[str] = None
    risk_weight: int
    sort_order: int
    applicable_doc_types: Optional[str] = None   # NULL = all doc types
    is_active: bool
    is_builtin: bool

    class Config:
        from_attributes = True


class FieldDefCreate(BaseModel):
    field_key: str
    display_label: str
    priority: str = "optional"
    extraction_keywords: Optional[str] = None
    risk_weight: int = 0
    sort_order: int = 99
    applicable_doc_types: Optional[str] = None


class FieldDefUpdate(BaseModel):
    display_label: Optional[str] = None
    priority: Optional[str] = None
    extraction_keywords: Optional[str] = None
    risk_weight: Optional[int] = None
    sort_order: Optional[int] = None
    applicable_doc_types: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("", response_model=list[FieldDefOut])
def list_field_defs(db: Session = Depends(get_db)):
    return (
        db.query(FieldDefinition)
        .order_by(FieldDefinition.sort_order, FieldDefinition.id)
        .all()
    )


@router.post("", response_model=FieldDefOut, status_code=201)
def create_field_def(body: FieldDefCreate, db: Session = Depends(get_db)):
    if db.query(FieldDefinition).filter(FieldDefinition.field_key == body.field_key).first():
        raise HTTPException(400, f"field_key '{body.field_key}' already exists")
    data = body.model_dump()
    data["applicable_doc_types"] = _validate_doc_types(data.get("applicable_doc_types"))
    fd = FieldDefinition(**data, is_builtin=False)
    db.add(fd)
    db.commit()
    db.refresh(fd)
    return fd


@router.patch("/{fd_id}", response_model=FieldDefOut)
def update_field_def(fd_id: int, body: FieldDefUpdate, db: Session = Depends(get_db)):
    fd = db.query(FieldDefinition).filter(FieldDefinition.id == fd_id).first()
    if not fd:
        raise HTTPException(404, "Field definition not found")
    updates = body.model_dump(exclude_unset=True)
    if "applicable_doc_types" in updates:
        updates["applicable_doc_types"] = _validate_doc_types(updates["applicable_doc_types"])
    for k, v in updates.items():
        setattr(fd, k, v)
    db.commit()
    db.refresh(fd)
    return fd


@router.delete("/{fd_id}")
def delete_field_def(fd_id: int, db: Session = Depends(get_db)):
    fd = db.query(FieldDefinition).filter(FieldDefinition.id == fd_id).first()
    if not fd:
        raise HTTPException(404, "Field definition not found")
    if fd.is_builtin:
        raise HTTPException(400, "Built-in field definitions cannot be deleted")
    db.delete(fd)
    db.commit()
    return {"ok": True}
