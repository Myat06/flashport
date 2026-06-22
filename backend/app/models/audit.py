import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String, nullable=False)        # e.g. "declaration.approved"
    entity_type = Column(String)                   # "declaration", "operator", etc.
    entity_id = Column(String)                     # UUID as string
    performed_by = Column(String)                  # "manager", operator_id, "system"
    detail = Column(JSON, default=dict)            # extra context
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
