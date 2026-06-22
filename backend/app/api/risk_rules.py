from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.risk_rule import RiskRule

router = APIRouter(prefix="/risk-rules", tags=["risk-rules"])


class RuleCreate(BaseModel):
    name: str
    field: str
    condition: str       # "starts_with" | "equals" | "missing" | "contains" | "gt"
    value: str = ""
    risk_boost: int = 10
    flag_label: str = ""


class RuleUpdate(BaseModel):
    name: str | None = None
    risk_boost: int | None = None
    flag_label: str | None = None
    is_active: bool | None = None


@router.get("")
def list_rules(db: Session = Depends(get_db)):
    rows = db.query(RiskRule).order_by(RiskRule.created_at.asc()).all()
    return [_out(r) for r in rows]


@router.post("", status_code=201)
def create_rule(body: RuleCreate, db: Session = Depends(get_db)):
    rule = RiskRule(
        name=body.name,
        field=body.field,
        condition=body.condition,
        value=body.value,
        risk_boost=body.risk_boost,
        flag_label=body.flag_label or body.name.lower().replace(" ", "_"),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return _out(rule)


@router.patch("/{rule_id}")
def update_rule(rule_id: str, body: RuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(RiskRule).filter(RiskRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    if body.name is not None:
        rule.name = body.name
    if body.risk_boost is not None:
        rule.risk_boost = body.risk_boost
    if body.flag_label is not None:
        rule.flag_label = body.flag_label
    if body.is_active is not None:
        rule.is_active = body.is_active
    db.commit()
    return _out(rule)


@router.delete("/{rule_id}")
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(RiskRule).filter(RiskRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"status": "deleted"}


def _out(r: RiskRule):
    return {
        "id": r.id,
        "name": r.name,
        "field": r.field,
        "condition": r.condition,
        "value": r.value,
        "risk_boost": r.risk_boost,
        "flag_label": r.flag_label,
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
