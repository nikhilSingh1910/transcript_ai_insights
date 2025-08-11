from typing import List, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Call(Base):
    __tablename__ = "calls"

    call_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(64), index=True)
    customer_id: Mapped[str] = mapped_column(String(64))
    language: Mapped[str] = mapped_column(String(16), default="en")
    start_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    transcript: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        ARRAY(Float), nullable=True
    )
    agent_talk_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    customer_sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
