def test_agents_leaderboard(client):
    resp = client.get("/api/v1/analytics/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    # A1 and A2 exist in seed
    agent_ids = {row["agent_id"] for row in data["items"]}
    assert "A1" in agent_ids
    assert "A2" in agent_ids
