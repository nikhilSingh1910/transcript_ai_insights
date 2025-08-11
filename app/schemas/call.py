from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, confloat, conint


# Query Schemas
class CallListQuery(BaseModel):
    limit: conint(ge=1, le=200) = 50
    offset: conint(ge=0) = 0
    agent_id: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    min_sentiment: Optional[confloat(ge=-1, le=1)] = None
    max_sentiment: Optional[confloat(ge=-1, le=1)] = None


# Response Schemas
class CallBase(BaseModel):
    call_id: str
    agent_id: Optional[str] = None
    customer_id: Optional[str] = None
    language: Optional[str] = None
    start_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    agent_talk_ratio: Optional[float] = Field(None, ge=0, le=1)
    customer_sentiment_score: Optional[float] = Field(None, ge=-1, le=1)


class CallDetail(CallBase):
    embedding: Optional[list[float]] = None


class CallListResponse(BaseModel):
    total: int
    items: List[CallBase]


class RecommendationItem(BaseModel):
    call_id: str
    similarity: float = Field(..., ge=0, le=1)


class RecommendationsResponse(BaseModel):
    base_call_id: str
    recommendations: List[RecommendationItem]
    coaching_nudges: List[str]


class AgentAggregate(BaseModel):
    agent_id: str
    avg_sentiment: Optional[float]
    avg_talk_ratio: Optional[float]
    total_calls: int


class AgentsLeaderboardResponse(BaseModel):
    items: List[AgentAggregate]
