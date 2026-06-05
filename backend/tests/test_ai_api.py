from fastapi.testclient import TestClient

import app.main_deps as deps
from app.main import app
from app.ai import FakeAI
from app.servicenow import FakeServiceNow


def teardown_function():
    app.dependency_overrides.clear()


def _client(sn):
    app.dependency_overrides[deps.get_sn] = lambda: sn
    app.dependency_overrides[deps.get_ai] = lambda: FakeAI(canned="S")
    return TestClient(app)


def test_summary_endpoint_and_status(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AI_ENABLED", "true")
    sn = FakeServiceNow()
    c = _client(sn)
    cid = c.post("/api/clients", json={"name": "Acme"}).json()["sys_id"]

    r = c.post(f"/api/ai/summary/client/{cid}")
    assert r.status_code == 200 and r.json()["summary"] == "S"

    assert c.post("/api/ai/summary/client/nope").status_code == 404

    status = c.get("/api/ai/status").json()
    assert status["enabled"] is True


def test_extract_contact_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AI_ENABLED", "true")
    c = _client(FakeServiceNow())

    r = c.post("/api/ai/extract/contact", json={"signature": "Jane Doe\njane@acme.com"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "jane@acme.com"
    assert "name" in body


def test_extract_contact_endpoint_gated_when_ai_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AI_ENABLED", "false")
    c = _client(FakeServiceNow())

    r = c.post("/api/ai/extract/contact", json={"signature": "Jane Doe\njane@acme.com"})
    assert r.status_code == 403


def test_draft_endpoint_enabled_unknown_and_gated(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AI_ENABLED", "true")
    sn = FakeServiceNow()
    c = _client(sn)
    cid = c.post("/api/clients", json={"name": "Acme"}).json()["sys_id"]

    r = c.post(f"/api/ai/draft/client/{cid}")
    assert r.status_code == 200 and r.json()["draft"] == "S"

    assert c.post("/api/ai/draft/client/nope").status_code == 404


def test_draft_endpoint_is_gated_when_ai_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AI_ENABLED", "false")
    sn = FakeServiceNow()
    c = _client(sn)
    cid = c.post("/api/clients", json={"name": "Acme"}).json()["sys_id"]

    assert c.post(f"/api/ai/draft/client/{cid}").status_code == 403


def test_summary_endpoint_is_gated_when_ai_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AI_ENABLED", "false")
    sn = FakeServiceNow()
    c = _client(sn)
    cid = c.post("/api/clients", json={"name": "Acme"}).json()["sys_id"]

    # ai_enabled is the real switch: the endpoint is blocked server-side, not just hidden in the UI.
    assert c.post(f"/api/ai/summary/client/{cid}").status_code == 403
    assert c.get("/api/ai/status").json()["enabled"] is False


def test_prioritize_endpoint_enabled(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AI_ENABLED", "true")
    sn = FakeServiceNow()
    c = _client(sn)

    r = c.post("/api/ai/prioritize")
    assert r.status_code == 200 and r.json()["suggestion"] == "S"


def test_prioritize_endpoint_is_gated_when_ai_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AI_ENABLED", "false")
    c = _client(FakeServiceNow())

    assert c.post("/api/ai/prioritize").status_code == 403
