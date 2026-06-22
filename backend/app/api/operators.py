from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.operator import Operator
from app.api.auth import hash_pin

router = APIRouter(prefix="/operators", tags=["operators"])


class OperatorCreate(BaseModel):
    employee_id: str
    name: str
    pin: str


class OperatorUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class PinReset(BaseModel):
    new_pin: str


@router.get("")
def list_operators(db: Session = Depends(get_db)):
    rows = db.query(Operator).order_by(Operator.created_at.desc()).all()
    return [_out(r) for r in rows]


@router.post("", status_code=201)
def create_operator(body: OperatorCreate, db: Session = Depends(get_db)):
    existing = db.query(Operator).filter(Operator.employee_id == body.employee_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Employee ID already exists")
    op = Operator(
        employee_id=body.employee_id.strip().upper(),
        name=body.name.strip(),
        pin_hash=hash_pin(body.pin),
    )
    db.add(op)
    db.commit()
    db.refresh(op)
    return _out(op)


@router.patch("/{employee_id}")
def update_operator(employee_id: str, body: OperatorUpdate, db: Session = Depends(get_db)):
    op = db.query(Operator).filter(Operator.employee_id == employee_id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")
    if body.name is not None:
        op.name = body.name.strip()
    if body.is_active is not None:
        op.is_active = body.is_active
    db.commit()
    return _out(op)


@router.post("/{employee_id}/reset-pin")
def reset_pin(employee_id: str, body: PinReset, db: Session = Depends(get_db)):
    op = db.query(Operator).filter(Operator.employee_id == employee_id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")
    op.pin_hash = hash_pin(body.new_pin)
    db.commit()
    return {"status": "pin_reset"}


@router.delete("/{employee_id}")
def deactivate_operator(employee_id: str, db: Session = Depends(get_db)):
    op = db.query(Operator).filter(Operator.employee_id == employee_id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")
    op.is_active = False
    db.commit()
    return {"status": "deactivated"}


def _out(op: Operator):
    return {
        "employee_id": op.employee_id,
        "name": op.name,
        "is_active": op.is_active,
        "created_at": op.created_at.isoformat() if op.created_at else None,
    }
