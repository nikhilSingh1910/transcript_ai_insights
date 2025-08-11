import json

import pytest


@pytest.mark.timeout(10)
def test_ws_sentiment_stream(client):
    # Grab any existing call_id
    items = client.get("/api/v1/calls?limit=1").json()["items"]
    assert items
    call_id = items[0]["call_id"]

    ws_path = f"/ws/sentiment/{call_id}"

    with client.websocket_connect(ws_path) as ws:
        # receive a couple of frames
        msg1 = json.loads(ws.receive_text())
        msg2 = json.loads(ws.receive_text())
        assert msg1["call_id"] == call_id
        assert "sentiment" in msg1
        assert -1.0 <= msg1["sentiment"] <= 1.0
        assert "ts" in msg1
        assert msg2["call_id"] == call_id
