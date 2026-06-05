from fastapi.testclient import TestClient

import app.main_deps as deps
from app.main import app
from app.servicenow import FakeServiceNow


def teardown_function():
    app.dependency_overrides.clear()


def test_briefing_endpoint_returns_sections():
    sn = FakeServiceNow()
    app.dependency_overrides[deps.get_sn] = lambda: sn
    c = TestClient(app)
    cid = c.post("/api/clients", json={"name": "Acme", "status": "active"}).json()["sys_id"]
    c.post("/api/tasks", json={"title": "Do it", "client": cid, "priority": "high", "status": "open"})

    r = c.get("/api/briefing")
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"date", "now_tasks", "todays_meetings", "reminders", "radar"}
    assert any(t["title"] == "Do it" for t in body["now_tasks"])
