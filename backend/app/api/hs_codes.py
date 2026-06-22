from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.hs_code import HsCodeReference

router = APIRouter(prefix="/hs-codes", tags=["hs-codes"])


class HsCodeCreate(BaseModel):
    code: str
    description: str = ""
    category: str = ""
    is_restricted: bool = False
    restriction_note: str = ""


@router.get("/validate/{code}")
def validate_hs_code(code: str, db: Session = Depends(get_db)):
    clean = code.strip()
    ref = db.query(HsCodeReference).filter(HsCodeReference.code == clean).first()
    if not ref:
        # Partial prefix match (first 4 digits)
        prefix = clean.replace(".", "")[:4]
        ref = db.query(HsCodeReference).filter(
            HsCodeReference.code.like(f"{prefix}%")
        ).first()

    if not ref:
        return {"valid": False, "code": clean, "message": "HS code not found in reference database"}

    return {
        "valid": True,
        "code": ref.code,
        "description": ref.description,
        "category": ref.category,
        "is_restricted": ref.is_restricted,
        "restriction_note": ref.restriction_note,
        "message": f"Restricted — {ref.restriction_note}" if ref.is_restricted else "Valid",
    }


@router.get("")
def list_hs_codes(
    search: str = Query(""),
    restricted_only: bool = False,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(HsCodeReference)
    if restricted_only:
        q = q.filter(HsCodeReference.is_restricted == True)  # noqa: E712
    if search:
        q = q.filter(
            HsCodeReference.code.ilike(f"%{search}%") |
            HsCodeReference.description.ilike(f"%{search}%")
        )
    return q.limit(limit).all()


@router.post("", status_code=201)
def add_hs_code(body: HsCodeCreate, db: Session = Depends(get_db)):
    existing = db.query(HsCodeReference).filter(HsCodeReference.code == body.code.strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Code already exists")
    ref = HsCodeReference(**body.model_dump())
    ref.code = body.code.strip()
    db.add(ref)
    db.commit()
    return {"code": ref.code, "description": ref.description}


@router.delete("/{code}")
def delete_hs_code(code: str, db: Session = Depends(get_db)):
    ref = db.query(HsCodeReference).filter(HsCodeReference.code == code).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(ref)
    db.commit()
    return {"status": "deleted"}
