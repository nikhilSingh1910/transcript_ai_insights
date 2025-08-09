# tests/conftest.py
import os
import uuid
import math
import pytest
from datetime import datetime, timedelta
from typing import List

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from main import app                     
from app.api.v1 import endpoints as ep   # to override get_db
from app.models.call import Base, Call

TEST_DB_URL = "postgresql://nikhilsingh:new_password@localhost:5432/transcript_ai_insights_test"

def _unit_vec(seed: int, dim: int = 384) -> List[float]:
    import random
    r = random.Random(seed)
    v = [r.random() for _ in range(dim)]
    norm = math.sqrt(sum(x*x for x in v)) or 1.0
    return [x / norm for x in v]

@pytest.fixture(scope="session")
def db_engine():
    if not TEST_DB_URL:
        pytest.skip("Set TEST_DATABASE_URL to run DB-backed tests (ARRAY(Float) requires Postgres).")
    engine = create_engine(TEST_DB_URL, poolclass=NullPool, future=True)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        conn.commit()
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    Base.metadata.drop_all(db_engine)
    Base.metadata.create_all(db_engine)
    return sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

@pytest.fixture(scope="function")
def db_session(db_session_factory):
    session = db_session_factory()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(db_session, monkeypatch) -> TestClient:
    now = datetime.utcnow()
    rows = [
        Call(
            call_id=uuid.uuid4(),
            agent_id="A1",
            customer_id=str(uuid.uuid4()),
            language="English",
            start_time=now - timedelta(minutes=30),
            duration_seconds=600,
            transcript="**Customer Service Agent:** Hello! **Customer:** I need help with my order.",
            embedding=_unit_vec(1),
            agent_talk_ratio=0.60,
            customer_sentiment_score=0.25,
        ),
        Call(
            call_id=uuid.uuid4(),
            agent_id="A2",
            customer_id=str(uuid.uuid4()),
            language="English",
            start_time=now - timedelta(minutes=20),
            duration_seconds=900,
            transcript="**Customer Service Agent:** Hi there. **Customer:** The app keeps crashing.",
            embedding=_unit_vec(2),
            agent_talk_ratio=0.72,
            customer_sentiment_score=-0.35,
        ),
        Call(
            call_id=uuid.uuid4(),
            agent_id="A1",
            customer_id=str(uuid.uuid4()),
            language="English",
            start_time=now - timedelta(minutes=10),
            duration_seconds=300,
            transcript="**Customer Service Agent:** Good day. **Customer:** Thanks, it works now.",
            embedding=None,
            agent_talk_ratio=0.40,
            customer_sentiment_score=0.90,
        ),
        Call(
            call_id=uuid.uuid4(),
            agent_id="A3",
            customer_id=str(uuid.uuid4()),
            language="English",
            start_time=now - timedelta(minutes=5),
            duration_seconds=450,
            transcript="**Customer Service Agent:** Welcome. **Customer:** Where is my refund?",
            embedding=_unit_vec(3),
            agent_talk_ratio=0.55,
            customer_sentiment_score=0.05,
        ),
    ]
    for r in rows:
        db_session.add(r)
    db_session.commit()

    # Overriding get_db to use the test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[ep.get_db] = override_get_db

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    return TestClient(app)
