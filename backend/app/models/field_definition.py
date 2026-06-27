from sqlalchemy import Boolean, Column, Integer, String, Text
from app.database import Base


class FieldDefinition(Base):
    __tablename__ = "field_definitions"

    id                  = Column(Integer, primary_key=True, index=True)
    field_key           = Column(String(100), unique=True, nullable=False)   # internal slug
    display_label       = Column(String(200), nullable=False)                # shown in UI
    priority            = Column(String(20), default="optional")             # critical/important/optional
    extraction_keywords = Column(Text)    # comma-separated keyword synonyms for OCR text search
    risk_weight         = Column(Integer, default=0)   # risk points added when field is missing
    sort_order           = Column(Integer, default=99)
    # NULL = applies to all doc types; comma-separated DocType values otherwise
    # e.g. "commercial_invoice,packing_list"
    applicable_doc_types = Column(Text, nullable=True)
    is_active            = Column(Boolean, default=True)
    is_builtin           = Column(Boolean, default=False)  # system fields cannot be deleted
