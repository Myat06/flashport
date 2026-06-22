from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit_logs(
    entity_id: str | None = Query(None),
    entity_type: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    rows = q.limit(limit).all()
    return [
        {
            "id": str(r.id),
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "performed_by": r.performed_by,
            "detail": r.detail,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
