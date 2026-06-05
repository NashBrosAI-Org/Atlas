from fastapi.testclient import TestClient

import app.main_deps as deps
from app.main import app
from app.ai import FakeAI
from app.servicenow import FakeServiceNow


def teardown_function():
    app.dependency_overrides.clear()


def test_summary_endpoint_and_status():
    sn = FakeServiceNow()
    app.dependency_overrides[deps.get_sn] = lambda: sn
    app.dependency_overrides[deps.get_ai] = lambda: FakeAI(canned="S")
    c = TestClient(app)
    cid = c.post("/api/clients", json={"name": "Acme"}).json()["sys_id"]

    r = c.post(f"/api/ai/summary/client/{cid}")
    assert r.status_code == 200 and r.json()["summary"] == "S"

    assert c.post("/api/ai/summary/client/nope").status_code == 404
    assert "enabled" in c.get("/api/ai/status").json()
