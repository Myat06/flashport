import uuid

from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class FieldValidationRule(Base):
    __tablename__ = "field_validation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    field_name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)   # required | regex | range | enum | max_length
    priority = Column(String, default="important")  # critical | important | optional
    min_val = Column(String)
    max_val = Column(String)
    pattern = Column(String)
    allowed_values = Column(String)  # comma-separated
    max_length = Column(Integer)
    error_message = Column(Text)
    is_active = Column(Boolean, default=True)
    is_builtin = Column(Boolean, default=False)  # built-ins can be toggled but not deleted
