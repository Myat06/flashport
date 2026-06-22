from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log(
    db: Session,
    action: str,
    entity_type: str = "",
    entity_id: str = "",
    performed_by: str = "system",
    detail: dict | None = None,
):
    db.add(AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        performed_by=performed_by,
        detail=detail or {},
    ))
