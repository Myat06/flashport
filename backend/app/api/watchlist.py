from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.watchlist import WatchlistEntry

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistCreate(BaseModel):
    entity_type: str   # "importer" | "exporter" | "hs_code"
    value: str
    reason: str = ""


@router.get("")
def list_watchlist(db: Session = Depends(get_db)):
    rows = db.query(WatchlistEntry).filter(WatchlistEntry.is_active == True).order_by(WatchlistEntry.created_at.desc()).all()  # noqa: E712
    return [
        {
            "id": r.id,
            "entity_type": r.entity_type,
            "value": r.value,
            "reason": r.reason,
            "added_by": r.added_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("", status_code=201)
def add_to_watchlist(body: WatchlistCreate, db: Session = Depends(get_db)):
    existing = db.query(WatchlistEntry).filter(
        WatchlistEntry.entity_type == body.entity_type,
        WatchlistEntry.value == body.value.strip(),
        WatchlistEntry.is_active == True,  # noqa: E712
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Entry already on watchlist")
    entry = WatchlistEntry(entity_type=body.entity_type, value=body.value.strip(), reason=body.reason)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"id": entry.id, "value": entry.value, "entity_type": entry.entity_type}


@router.delete("/{entry_id}")
def remove_from_watchlist(entry_id: str, db: Session = Depends(get_db)):
    entry = db.query(WatchlistEntry).filter(WatchlistEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    entry.is_active = False
    db.commit()
    return {"status": "removed"}


@router.get("/check")
def check_watchlist(importer: str = "", exporter: str = "", hs_code: str = "", db: Session = Depends(get_db)):
    hits = []
    checks = [("importer", importer), ("exporter", exporter), ("hs_code", hs_code)]
    for etype, val in checks:
        if not val:
            continue
        match = db.query(WatchlistEntry).filter(
            WatchlistEntry.entity_type == etype,
            WatchlistEntry.value.ilike(val.strip()),
            WatchlistEntry.is_active == True,  # noqa: E712
        ).first()
        if match:
            hits.append({"entity_type": etype, "value": val, "reason": match.reason})
    return {"hits": hits, "flagged": len(hits) > 0}
