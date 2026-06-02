def test_now_orders_by_priority_then_due(client):
    client.post("/api/tasks", json={"title": "low-soon", "priority": "low", "due_date": "2026-06-03"})
    client.post("/api/tasks", json={"title": "crit-later", "priority": "critical", "due_date": "2026-06-30"})
    client.post("/api/tasks", json={"title": "high-nodate", "priority": "high"})
    client.post("/api/tasks", json={"title": "done-task", "priority": "critical", "status": "done"})

    rows = client.get("/api/now").json()
    titles = [t["title"] for t in rows]
    assert "done-task" not in titles                      # done excluded
    assert titles[0] == "crit-later"                       # critical first
    assert titles.index("high-nodate") < titles.index("low-soon")

def test_now_commitment_breaks_ties(client):
    # Same priority and same due_date — the commitment must sort first.
    client.post("/api/tasks", json={"title": "plain", "priority": "high", "due_date": "2026-06-10"})
    client.post("/api/tasks", json={"title": "promised", "priority": "high", "due_date": "2026-06-10", "is_commitment": True})

    titles = [t["title"] for t in client.get("/api/now").json()]
    assert titles.index("promised") < titles.index("plain")


def test_now_filters_by_client(client):
    client.post("/api/tasks", json={"title": "for-a", "client": "A"})
    client.post("/api/tasks", json={"title": "for-b", "client": "B"})
    rows = client.get("/api/now?client=A").json()
    assert [t["title"] for t in rows] == ["for-a"]
