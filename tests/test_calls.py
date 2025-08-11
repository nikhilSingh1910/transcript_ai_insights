from datetime import datetime, timedelta


def test_list_calls_basic(client):
    resp = client.get("/api/v1/calls?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data and "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 10


def test_list_calls_filters(client):
    # filter by agent_id
    r1 = client.get("/api/v1/calls", params={"agent_id": "A1"})
    assert r1.status_code == 200
    items = r1.json()["items"]
    assert all(it["agent_id"] == "A1" for it in items)

    # filter by sentiment range
    r2 = client.get(
        "/api/v1/calls", params={"min_sentiment": 0.2, "max_sentiment": 1.0}
    )
    assert r2.status_code == 200
    items2 = r2.json()["items"]
    for it in items2:
        s = it["customer_sentiment_score"]
        assert s is None or (0.2 <= s <= 1.0)


def test_get_call_404(client):
    resp = client.get("/api/v1/calls/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_get_call_detail_ok(client):
    # use one id from list
    lst = client.get("/api/v1/calls?limit=1").json()["items"]
    assert lst
    call_id = lst[0]["call_id"]
    resp = client.get(f"/api/v1/calls/{call_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["call_id"] == call_id
    assert "embedding" in detail  # exposed by schema
