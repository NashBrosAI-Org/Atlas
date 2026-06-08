"""The 'Claude bridge' ingestion path: Graph-shaped payloads POSTed by an external
caller run through the same pipeline as the live /sync. Logic tests against the
fakes + an API test through the route."""
import pytest
from fastapi.testclient import TestClient

import app.main_deps as deps
from app import m365
from app.main import app
from app.servicenow import FakeServiceNow

SCOPE = "x_atlas_sn"

MSG = {
    "id": "g-msg-1", "subject": "Renewal question",
    "receivedDateTime": "2026-06-04T09:00:00Z",
    "from": {"emailAddress": {"address": "jane@acme.com"}},
    "toRecipients": [{"emailAddress": {"address": "me@firm.com"}}],
    "body": {"contentType": "text", "content": "Can we discuss the renewal?"},
    "flag": {"flagStatus": "flagged"},
}
EVT = {
    "id": "g-evt-1", "subject": "Acme QBR",
    "start": {"dateTime": "2026-06-10T15:00:00Z"},
    "attendees": [{"emailAddress": {"address": "jane@acme.com"}}],
    "isOnlineMeeting": True,
}


async def _seed_acme(sn):
    return (await sn.create(f"{SCOPE}_client",
                            {"name": "Acme", "email_domains": "acme.com"}))["sys_id"]


@pytest.mark.asyncio
async def test_ingest_payload_handles_mail_and_calendar_and_associates():
    sn = FakeServiceNow()
    cid = await _seed_acme(sn)

    result = await m365.ingest_payload(sn, SCOPE, messages=[MSG], events=[EVT])

    assert result["mail"] == {"ingested": 1, "skipped": 0, "tasks_created": 1}
    assert result["calendar"] == {"ingested": 1, "skipped": 0}

    email = (await sn.list(f"{SCOPE}_email"))[0]
    assert email["graph_message_id"] == "g-msg-1" and email["client"] == cid
    meeting = (await sn.list(f"{SCOPE}_meeting"))[0]
    assert meeting["graph_event_id"] == "g-evt-1" and meeting["client"] == cid
    # flagged mail raised exactly one follow-up task
    assert [t["title"] for t in await sn.list(f"{SCOPE}_task")] == ["Follow up: Renewal question"]


@pytest.mark.asyncio
async def test_ingest_payload_is_idempotent_and_partial():
    sn = FakeServiceNow()
    await _seed_acme(sn)

    # events omitted → only mail processed, no "calendar" key
    first = await m365.ingest_payload(sn, SCOPE, messages=[MSG])
    assert first == {"mail": {"ingested": 1, "skipped": 0, "tasks_created": 1}}

    # re-posting the same message dedups on graph_message_id
    again = await m365.ingest_payload(sn, SCOPE, messages=[MSG])
    assert again["mail"] == {"ingested": 0, "skipped": 1, "tasks_created": 0}
    assert len(await sn.list(f"{SCOPE}_email")) == 1


def teardown_function():
    app.dependency_overrides.clear()


def test_ingest_endpoint_runs_pipeline():
    sn = FakeServiceNow()
    app.dependency_overrides[deps.get_sn] = lambda: sn
    c = TestClient(app)
    c.post("/api/clients", json={"name": "Acme", "email_domains": "acme.com"})

    r = c.post("/api/m365/ingest", json={"messages": [MSG], "events": [EVT]})
    assert r.status_code == 200
    body = r.json()
    assert body["mail"]["ingested"] == 1 and body["calendar"]["ingested"] == 1

    # empty payload is a valid no-op
    r2 = c.post("/api/m365/ingest", json={})
    assert r2.status_code == 200 and r2.json() == {}
