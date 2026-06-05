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


def test_search_endpoint_returns_hits(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    cid = c.post("/api/clients", json={"name": "Acme", "status": "active"}).json()["sys_id"]
    c.post("/api/tasks", json={"title": "Acme renewal", "client": cid})

    r = c.get("/api/search?q=acme")
    assert r.status_code == 200
    hits = r.json()
    assert any(h["type"] == "task" and h["label"] == "Acme renewal" for h in hits)
    task_hit = next(h for h in hits if h["type"] == "task")
    assert task_hit["client"] == cid and task_hit["client_name"] == "Acme"


def test_search_empty_query_returns_empty(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    c.post("/api/clients", json={"name": "Acme", "status": "active"})
    r = c.get("/api/search?q=")
    assert r.status_code == 200
    assert r.json() == []


def test_search_types_param_filters(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    cid = c.post("/api/clients", json={"name": "Acme", "status": "active"}).json()["sys_id"]
    c.post("/api/tasks", json={"title": "Acme task", "client": cid})
    r = c.get("/api/search?q=acme&types=task")
    assert r.status_code == 200
    assert {h["type"] for h in r.json()} == {"task"}
