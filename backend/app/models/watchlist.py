import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.database import Base


class WatchlistEntry(Base):
    __tablename__ = "watchlist"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String, nullable=False)   # "importer" | "exporter" | "hs_code"
    value = Column(String, nullable=False)          # the name or code to watch
    reason = Column(Text)
    added_by = Column(String, default="manager")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
