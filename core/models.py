from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import String, DateTime, func
from datetime import datetime
from core.database import Base

class RawMatchTimeline(Base):
    __tablename__ = "raw_match_timelines"

    match_id = Column(String, primary_key=True, index=True)
    queue_id = Column(Integer, index=True)  # La nouvelle colonne indexee
    raw_data = Column(JSON, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())