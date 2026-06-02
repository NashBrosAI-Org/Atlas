def test_create_and_list_tasks(client):
    r = client.post("/api/tasks", json={"title": "Send SOW", "priority": "high", "is_commitment": True})
    assert r.status_code == 201
    assert r.json()["sys_id"]
    rows = client.get("/api/tasks").json()
    assert any(t["title"] == "Send SOW" for t in rows)

def test_update_task_status(client):
    sid = client.post("/api/tasks", json={"title": "X"}).json()["sys_id"]
    r = client.patch(f"/api/tasks/{sid}", json={"status": "done"})
    assert r.status_code == 200
    assert r.json()["status"] == "done"
