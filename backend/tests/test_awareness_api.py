from fastapi.testclient import TestClient

import app.user_config as uc
import app.main_deps as deps
from app.main import app
from app.servicenow import FakeServiceNow


def _client(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(uc, "get_password", lambda: None)
    sn = FakeServiceNow()
    app.dependency_overrides[deps.get_sn] = lambda: sn
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_activity_timeline_and_radar(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    cid = c.post("/api/clients", json={"name": "Acme", "status": "active"}).json()["sys_id"]
    c.post("/api/tasks", json={"title": "T1", "client": cid})

    act = c.get("/api/awareness/activity")
    assert act.status_code == 200
    assert any(e["title"] == "Task: T1" for e in act.json())

    tl = c.get(f"/api/awareness/timeline/{cid}")
    assert tl.status_code == 200
    assert len(tl.json()) == 1 and tl.json()[0]["title"] == "Task: T1"

    assert c.get("/api/awareness/timeline/does-not-exist").status_code == 404

    radar = c.get("/api/awareness/radar")
    assert radar.status_code == 200
    assert isinstance(radar.json(), list)


def test_activity_limit_param(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    cid = c.post("/api/clients", json={"name": "Acme", "status": "active"}).json()["sys_id"]
    for i in range(4):
        c.post("/api/tasks", json={"title": f"t{i}", "client": cid})
    assert len(c.get("/api/awareness/activity?limit=2").json()) == 2
