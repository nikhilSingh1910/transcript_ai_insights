from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

Limit = Annotated[int, Field(ge=1, le=200)]
Offset = Annotated[int, Field(ge=0)]
Sentiment = Annotated[float, Field(ge=-1.0, le=1.0)]
TalkRatio = Annotated[float, Field(ge=0.0, le=1.0)]


#  Query Schemas
class CallListQuery(BaseModel):
    limit: Limit = 50
    offset: Offset = 0
    agent_id: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    min_sentiment: Optional[Sentiment] = None
    max_sentiment: Optional[Sentiment] = None


#  Response Schemas
class CallBase(BaseModel):
    call_id: UUID
    agent_id: Optional[str] = None
    customer_id: Optional[str] = None
    language: Optional[str] = None
    start_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    agent_talk_ratio: Optional[TalkRatio] = None
    customer_sentiment_score: Optional[Sentiment] = None

    model_config = dict(from_attributes=True)


class CallDetail(CallBase):
    embedding: Optional[list[float]] = None


class CallListResponse(BaseModel):
    total: int
    items: List[CallBase]


class RecommendationItem(BaseModel):
    call_id: UUID
    similarity: Annotated[float, Field(ge=0.0, le=1.0)]


class RecommendationsResponse(BaseModel):
    base_call_id: UUID
    recommendations: List[RecommendationItem]
    coaching_nudges: List[str]


class AgentAggregate(BaseModel):
    agent_id: str
    avg_sentiment: Optional[float]
    avg_talk_ratio: Optional[float]
    total_calls: int


class AgentsLeaderboardResponse(BaseModel):
    items: List[AgentAggregate]
