from fastapi.testclient import TestClient

import app.main_deps as deps
from app.main import app
from app.graph import FakeGraph
from app.servicenow import FakeServiceNow

MSG = {"id": "g1", "subject": "Hi", "receivedDateTime": "2026-06-04T09:00:00Z",
       "from": {"emailAddress": {"address": "jane@acme.com"}},
       "flag": {"flagStatus": "flagged"}}


def teardown_function():
    app.dependency_overrides.clear()


def test_sync_ingests_then_is_idempotent():
    sn = FakeServiceNow()
    app.dependency_overrides[deps.get_sn] = lambda: sn
    app.dependency_overrides[deps.get_graph] = lambda: FakeGraph(messages=[MSG])
    c = TestClient(app)
    c.post("/api/clients", json={"name": "Acme", "email_domains": "acme.com"})

    first = c.post("/api/m365/sync")
    assert first.status_code == 200
    assert first.json()["ingested"] == 1
    assert first.json()["tasks_created"] == 1

    again = c.post("/api/m365/sync")
    assert again.json()["ingested"] == 0 and again.json()["skipped"] == 1
