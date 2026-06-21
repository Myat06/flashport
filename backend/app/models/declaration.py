import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ConfidenceLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class RiskLevel(str, enum.Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


class JalurType(str, enum.Enum):
    hijau = "hijau"
    kuning = "kuning"
    merah = "merah"


class DocType(str, enum.Enum):
    commercial_invoice = "commercial_invoice"
    bill_of_lading = "bill_of_lading"
    packing_list = "packing_list"


class Declaration(Base):
    __tablename__ = "declarations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    document_type = Column(Enum(DocType), nullable=False)
    operator_id = Column(String)
    device_id = Column(String)
    fcm_token = Column(String)
    scanned_at = Column(DateTime(timezone=True), nullable=False)
    synced_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ml_kit_text = Column(Text)
    tesseract_text = Column(Text)
    confidence_badge = Column(Enum(ConfidenceLevel))
    risk_score = Column(Integer)
    risk_badge = Column(Enum(RiskLevel))
    flagged_fields = Column(JSON, default=list)
    ceisa_ready = Column(Boolean, default=False)
    reviewed_by = Column(String)
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    fields = relationship("DeclarationField", back_populates="declaration", cascade="all, delete-orphan")
    submissions = relationship("CeisaSubmission", back_populates="declaration")


class DeclarationField(Base):
    __tablename__ = "declaration_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    declaration_id = Column(UUID(as_uuid=True), ForeignKey("declarations.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String, nullable=False)
    field_value = Column(Text)
    is_edited = Column(Boolean, default=False)
    edit_source = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    declaration = relationship("Declaration", back_populates="fields")


class CeisaSubmission(Base):
    __tablename__ = "ceisa_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    declaration_id = Column(UUID(as_uuid=True), ForeignKey("declarations.id"), nullable=False)
    submitted_by = Column(String)
    submitted_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    jalur = Column(Enum(JalurType))
    response_code = Column(String)
    response_message = Column(String)
    raw_response = Column(JSON)

    declaration = relationship("Declaration", back_populates="submissions")


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), nullable=False)
    device_id = Column(String)
    image_size_bytes = Column(Integer)
    ml_kit_char_count = Column(Integer)
    sync_duration_ms = Column(Integer)
    status = Column(String)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
