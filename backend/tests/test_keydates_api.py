from fastapi.testclient import TestClient

import app.main_deps as deps
from app.main import app
from app.servicenow import FakeServiceNow


def _client():
    sn = FakeServiceNow()
    app.dependency_overrides[deps.get_sn] = lambda: sn
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_key_date_crud_and_reminders():
    c = _client()
    cid = c.post("/api/clients", json={"name": "Acme", "status": "active"}).json()["sys_id"]

    created = c.post("/api/key-dates", json={
        "title": "Renewal", "type": "renewal", "date": "2099-01-01",
        "reminder_lead_days": 7, "client": cid})
    assert created.status_code == 201
    kid = created.json()["sys_id"]

    # CRUD round-trips through the generic factory.
    assert c.get("/api/key-dates").json()[0]["title"] == "Renewal"
    assert c.get(f"/api/key-dates?client={cid}").json()[0]["sys_id"] == kid
    assert c.get(f"/api/key-dates/{kid}").json()["type"] == "renewal"

    # A far-future, non-recurring date is outside the reminder window.
    assert c.get("/api/reminders").json() == []

    # A recurring date with a huge lead is always within the window (deterministic
    # regardless of the real "today" the endpoint uses).
    c.post("/api/key-dates", json={"title": "Soon", "date": "2000-02-15",
                                   "recurring": True, "reminder_lead_days": 3650, "client": cid})
    rems = c.get("/api/reminders").json()
    assert any(r["title"] == "Soon" for r in rems)
