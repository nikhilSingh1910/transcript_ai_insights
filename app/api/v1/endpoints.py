from __future__ import annotations

import math
import os
from typing import List

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.call import Call
from app.schemas.call import (
    AgentAggregate,
    AgentsLeaderboardResponse,
    CallBase,
    CallDetail,
    CallListQuery,
    CallListResponse,
    RecommendationItem,
    RecommendationsResponse,
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    try:
        import openai

        openai.api_key = OPENAI_API_KEY
    except Exception:
        OPENAI_API_KEY = None

# API router for all `/api/v1/calls` endpoints
router = APIRouter(prefix="/api/v1", tags=["calls"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper functions


def _cosine_similarity_calculator(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two embedding vectors.
    Returns 0.0 if either vector has zero length.
    """
    denom = np.linalg.norm(a) * np.linalg.norm(b)

    if denom == 0.0:
        return 0.0

    return float(np.dot(a, b) / denom)


def _to_np(vec):
    """
    Convert a Python list (or similar) to a NumPy array of floats.
    Returns None if conversion fails.
    """
    try:
        return np.asarray(vec, dtype=np.float32)
    except Exception:
        return None


def _make_nudges(call: Call, neighbors: list[Call]) -> list[str]:
    """
    Generate ≤ 3 short coaching nudges ≤ 40 words each. If OPENAI_API_KEY is present, ask for 3 nudges; else rule-based.
    """

    sent = call.customer_sentiment_score
    ratio = call.agent_talk_ratio
    transcript = (call.transcript or "")[:600]

    if OPENAI_API_KEY:
        try:
            prompt = (
                "You are a sales coaching assistant. Provide exactly three concise coaching nudges "
                "(each <= 40 words) for a call based on:\n"
                f"- customer_sentiment_score (−1..+1): {sent}\n"
                f"- agent_talk_ratio (0..1): {ratio}\n"
                f"- snippet: ```{transcript}```\n"
                "Number them 1-3. No preamble."
            )

            resp = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.2,
            )

            text = resp["choices"][0]["message"]["content"].strip()

            # Split lines, sanitize to <= 3 nudges
            lines = [l.strip("-• ").strip() for l in text.splitlines() if l.strip()]

            nudges: List[str] = []
            for ln in lines:
                if len(nudges) >= 3:
                    break
                if len(ln.split()) <= 40:
                    nudges.append(ln)

            if nudges:
                return nudges[:3]
        except Exception as e:
            print("e", e)
            pass

    # Fallback rule-based nudges
    nudges = []
    if ratio is not None:
        if ratio > 0.65:
            nudges.append(
                "Talk less; ask one open-ended question after each explanation to invite the customer to speak more."
            )
        elif ratio < 0.35:
            nudges.append(
                "Guide the call with a brief summary and propose next steps to keep momentum."
            )
    if sent is not None:
        if sent < -0.2:
            nudges.append(
                "Acknowledge frustration explicitly, then offer a clear fix and a time-bound follow-up."
            )
        elif sent < 0.2:
            nudges.append(
                "Check for understanding and confirm value before closing to lift sentiment."
            )
        else:
            nudges.append(
                "Reinforce benefits and confirm next step while the customer is positive."
            )
    if not nudges:
        nudges.append(
            "Clarify the problem, confirm expectations, and summarize next actions in one sentence."
        )
    # ensure 3 max
    return nudges[:3]


# API Endpoints


@router.get("/calls", response_model=CallListResponse)
def get_all_calls(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    agent_id: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    min_sentiment: float | None = Query(None, ge=-1, le=1),
    max_sentiment: float | None = Query(None, ge=-1, le=1),
    db: Session = Depends(get_db),
):
    """
    Return a paginated list of calls.
    Supports filtering by:
    - agent_id
    - date range
    - sentiment score range
    """
    q = db.query(Call)

    if agent_id:
        q = q.filter(Call.agent_id == agent_id)
    if from_date:
        q = q.filter(Call.start_time >= from_date)
    if to_date:
        q = q.filter(Call.start_time <= to_date)
    if min_sentiment is not None:
        q = q.filter(Call.customer_sentiment_score >= min_sentiment)
    if max_sentiment is not None:
        q = q.filter(Call.customer_sentiment_score <= max_sentiment)

    total = q.count()
    rows: List[Call] = (
        q.order_by(Call.start_time.desc()).limit(limit).offset(offset).all()
    )

    items = [
        CallBase(
            call_id=str(r.call_id),
            agent_id=r.agent_id,
            customer_id=r.customer_id,
            language=r.language,
            start_time=r.start_time,
            duration_seconds=r.duration_seconds,
            transcript=r.transcript,
            agent_talk_ratio=r.agent_talk_ratio,
            customer_sentiment_score=r.customer_sentiment_score,
        )
        for r in rows
    ]
    return CallListResponse(total=total, items=rows)


@router.get("/calls/{call_id}", response_model=CallDetail)
def get_call(call_id: str, db: Session = Depends(get_db)):
    """
    Fetch full details of a single call by its ID.
    """
    call = db.query(Call).filter(Call.call_id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="call not found")
    return CallDetail(
        call_id=str(call.call_id),
        agent_id=call.agent_id,
        customer_id=call.customer_id,
        language=call.language,
        start_time=call.start_time,
        duration_seconds=call.duration_seconds,
        transcript=call.transcript,
        agent_talk_ratio=call.agent_talk_ratio,
        customer_sentiment_score=call.customer_sentiment_score,
        embedding=call.embedding,
    )


@router.get("/calls/{call_id}/recommendations", response_model=RecommendationsResponse)
def get_recommendations(call_id: str, db: Session = Depends(get_db)):
    """
    Find the top 5 most similar calls (based on cosine similarity of embeddings)
    and generate 3 coaching nudges for the agent.
    """
    base = db.query(Call).filter(Call.call_id == call_id).first()
    if not base:
        raise HTTPException(status_code=404, detail="call not found")
    if not base.embedding:
        raise HTTPException(status_code=409, detail="base call missing embedding")

    base_vec = _to_np(base.embedding)
    if base_vec is None:
        raise HTTPException(status_code=409, detail="invalid base embedding")

    # fetch other calls with embeddings
    similar_calls: List[Call] = (
        db.query(Call)
        .filter(and_(Call.call_id != call_id, Call.embedding.isnot(None)))
        .limit(1000)
        .all()
    )

    scored: list[tuple[str, float]] = []
    for c in similar_calls:
        vec = _to_np(c.embedding)
        if vec is None:
            continue
        sim = _cosine_similarity_calculator(base_vec, vec)
        scored.append((str(c.call_id), sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:5]
    rec_items = [RecommendationItem(call_id=cid, similarity=sim) for cid, sim in top]

    nudges: list[str] = _make_nudges(
        base, [c for c in similar_calls if str(c.call_id) in {cid for cid, _ in top}]
    )

    return RecommendationsResponse(
        base_call_id=str(base.call_id),
        recommendations=rec_items,
        coaching_nudges=nudges,
    )


@router.get("/analytics/agents", response_model=AgentsLeaderboardResponse)
def get_agents_leaderboard(db: Session = Depends(get_db)):
    """
    Return per-agent aggregated metrics:
    - Average customer sentiment
    - Average agent talk ratio
    - Total number of calls
    Sorted by number of calls (descending).
    """
    # Aggregate by agent: avg sentiment, avg talk ratio, count
    rows = (
        db.query(
            Call.agent_id,
            func.avg(Call.customer_sentiment_score),
            func.avg(Call.agent_talk_ratio),
            func.count(Call.call_id),
        )
        .group_by(Call.agent_id)
        .order_by(func.count(Call.call_id).desc())
        .all()
    )

    items = [
        AgentAggregate(
            agent_id=r[0],
            avg_sentiment=(float(r[1]) if r[1] is not None else None),
            avg_talk_ratio=(float(r[2]) if r[2] is not None else None),
            total_calls=int(r[3]),
        )
        for r in rows
    ]
    return AgentsLeaderboardResponse(items=items)
