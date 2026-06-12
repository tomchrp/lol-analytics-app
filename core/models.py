from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import String, DateTime, func
from datetime import datetime
from core.database import Base

class RawMatchTimeline(Base):
    __tablename__ = "raw_match_timelines"

    match_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )