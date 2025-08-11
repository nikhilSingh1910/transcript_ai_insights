from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Call(Base):
    __tablename__ = "calls"

    call_id = Column(UUID(as_uuid=True), primary_key=True)
    agent_id = Column(String, index=True)
    customer_id = Column(String)
    language = Column(String)
    start_time = Column(DateTime, index=True)
    duration_seconds = Column(Integer)
    transcript = Column(Text)
    embedding = Column(ARRAY(Float), nullable=True)
    agent_talk_ratio = Column(Float, nullable=True)
    customer_sentiment_score = Column(Float, nullable=True)
