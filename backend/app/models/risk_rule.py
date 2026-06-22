import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.database import Base


class RiskRule(Base):
    __tablename__ = "risk_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    field = Column(String, nullable=False)         # "hs_code", "importer", "invoice_value", etc.
    condition = Column(String, nullable=False)     # "starts_with", "equals", "missing", "gt"
    value = Column(Text, default="")               # the value to match
    risk_boost = Column(Integer, default=10)       # points added to risk score
    flag_label = Column(String)                    # label added to flagged_fields
    is_active = Column(Boolean, default=True)
    created_by = Column(String, default="manager")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
