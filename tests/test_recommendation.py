def _find_with_embedding(client):
    data = client.get("/api/v1/calls?limit=50").json()
    for it in data["items"]:
        detail = client.get(f"/api/v1/calls/{it['call_id']}").json()
        if detail["embedding"] is not None:
            return it["call_id"]
    return None

def test_recommendations_ok(client):
    call_id = _find_with_embedding(client)
    assert call_id is not None
    resp = client.get(f"/api/v1/calls/{call_id}/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["base_call_id"] == call_id
    assert 0 <= len(data["recommendations"]) <= 5
    # nudges are rule-based in tests (OPENAI_API_KEY unset)
    assert 1 <= len(data["coaching_nudges"]) <= 3
