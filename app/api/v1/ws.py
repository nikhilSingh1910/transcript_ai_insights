import asyncio
import json
import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.call import Call

ws_router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@ws_router.websocket("/ws/sentiment/{call_id}")
async def ws_sentiment(
    websocket: WebSocket, call_id: str, db: Session = Depends(get_db)
):
    """
    - Accepts a WebSocket connection at /ws/sentiment/{call_id}
    - Seeds the stream from the stored sentiment (or a small positive baseline)
    - Emits an updated sentiment value once per second for ~2 minutes
    - Values follow a bounded random walk in [-1, 1]
    """
    await websocket.accept()

    call = db.query(Call).filter(Call.call_id == call_id).first()
    base = (
        call.customer_sentiment_score
        if call and call.customer_sentiment_score is not None
        else 0.1
    )
    value = float(base)

    try:
        for _ in range(120):  # once per second for ~2 minutes

            step = random.uniform(-0.08, 0.08)
            value = max(-1.0, min(1.0, value + step))
            payload = {
                "call_id": call_id,
                "sentiment": round(value, 4),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
