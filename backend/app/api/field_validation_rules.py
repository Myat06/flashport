from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.field_validation_rule import FieldValidationRule

router = APIRouter(prefix="/field-validation-rules", tags=["field-validation-rules"])


class RuleOut(BaseModel):
    id: UUID
    name: str
    field_name: str
    rule_type: str
    priority: str
    min_val: Optional[str] = None
    max_val: Optional[str] = None
    pattern: Optional[str] = None
    allowed_values: Optional[str] = None
    max_length: Optional[int] = None
    error_message: Optional[str] = None
    is_active: bool
    is_builtin: bool

    class Config:
        from_attributes = True


class RuleCreate(BaseModel):
    name: str
    field_name: str
    rule_type: str
    priority: str = "important"
    min_val: Optional[str] = None
    max_val: Optional[str] = None
    pattern: Optional[str] = None
    allowed_values: Optional[str] = None
    max_length: Optional[int] = None
    error_message: Optional[str] = None


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[str] = None
    min_val: Optional[str] = None
    max_val: Optional[str] = None
    pattern: Optional[str] = None
    allowed_values: Optional[str] = None
    max_length: Optional[int] = None
    error_message: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("", response_model=list[RuleOut])
def list_rules(db: Session = Depends(get_db)):
    return db.query(FieldValidationRule).order_by(
        FieldValidationRule.field_name, FieldValidationRule.name
    ).all()


@router.post("", response_model=RuleOut, status_code=201)
def create_rule(body: RuleCreate, db: Session = Depends(get_db)):
    rule = FieldValidationRule(**body.model_dump(), is_builtin=False)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: UUID, body: RuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(FieldValidationRule).filter(FieldValidationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: UUID, db: Session = Depends(get_db)):
    rule = db.query(FieldValidationRule).filter(FieldValidationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    if rule.is_builtin:
        raise HTTPException(status_code=400, detail="Built-in rules cannot be deleted — toggle is_active instead")
    db.delete(rule)
    db.commit()
