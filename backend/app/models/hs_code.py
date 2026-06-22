from sqlalchemy import Boolean, Column, String, Text

from app.database import Base


class HsCodeReference(Base):
    __tablename__ = "hs_code_reference"

    code = Column(String, primary_key=True)        # e.g. "8471.30.00"
    description = Column(Text)
    category = Column(String)                      # e.g. "Electronics", "Chemicals"
    is_restricted = Column(Boolean, default=False)
    restriction_note = Column(Text)
