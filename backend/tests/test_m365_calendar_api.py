from fastapi.testclient import TestClient

import app.main_deps as deps
from app.main import app
from app.graph import FakeGraph
from app.servicenow import FakeServiceNow

EVT = {"id": "e1", "subject": "QBR", "start": {"dateTime": "2026-06-05T15:00:00Z"},
       "attendees": [{"emailAddress": {"address": "jane@acme.com"}}], "isOnlineMeeting": True}


def teardown_function():
    app.dependency_overrides.clear()


def test_calendar_sync_then_prep():
    sn = FakeServiceNow()
    app.dependency_overrides[deps.get_sn] = lambda: sn
    app.dependency_overrides[deps.get_graph] = lambda: FakeGraph(events=[EVT])
    c = TestClient(app)
    c.post("/api/clients", json={"name": "Acme", "email_domains": "acme.com"})

    synced = c.post("/api/m365/calendar/sync",
                    params={"start": "2026-06-01T00:00:00Z", "end": "2026-06-30T00:00:00Z"})
    assert synced.status_code == 200 and synced.json()["ingested"] == 1

    meetings = c.get("/api/meetings").json()
    mid = meetings[0]["sys_id"]
    prep = c.get(f"/api/m365/prep/{mid}")
    assert prep.status_code == 200
    assert prep.json()["meeting"]["title"] == "QBR"
    assert prep.json()["client"]["name"] == "Acme"

    assert c.get("/api/m365/prep/nope").status_code == 404
