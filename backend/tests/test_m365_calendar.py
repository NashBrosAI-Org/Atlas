import pytest
from app import m365
from app.config import get_settings
from app.graph import FakeGraph
from app.servicenow import FakeServiceNow

SCOPE = get_settings().sn_scope

EVT = {
    "id": "evt-1", "subject": "QBR with Acme",
    "start": {"dateTime": "2026-06-05T15:00:00Z", "timeZone": "UTC"},
    "attendees": [
        {"emailAddress": {"address": "jane@acme.com", "name": "Jane"}},
        {"emailAddress": {"address": "me@firm.com", "name": "Me"}},
    ],
    "isOnlineMeeting": True,
}


def test_normalize_event_maps_to_meeting_row():
    row = m365.normalize_event(EVT)
    assert row["graph_event_id"] == "evt-1"
    assert row["title"] == "QBR with Acme"
    assert row["datetime"] == "2026-06-05T15:00:00Z"
    assert row["attendees"] == "jane@acme.com, me@firm.com"
    assert row["type"] == "teams"


def test_normalize_event_non_online_is_other():
    row = m365.normalize_event({**EVT, "isOnlineMeeting": False})
    assert row["type"] == "other"


async def _seed_client(sn):
    return (await sn.create(f"{SCOPE}_client",
                            {"name": "Acme", "email_domains": "acme.com"}))["sys_id"]


@pytest.mark.asyncio
async def test_ingest_events_idempotent_and_associates_by_attendee_domain():
    sn = FakeServiceNow()
    cid = await _seed_client(sn)
    graph = FakeGraph(events=[EVT])

    first = await m365.ingest_events(graph, sn, SCOPE,
                                     "2026-06-01T00:00:00Z", "2026-06-30T00:00:00Z")
    assert first == {"ingested": 1, "skipped": 0}

    meetings = await sn.list(f"{SCOPE}_meeting")
    assert len(meetings) == 1
    assert meetings[0]["graph_event_id"] == "evt-1"
    assert meetings[0]["client"] == cid        # associated via jane@acme.com

    again = await m365.ingest_events(graph, sn, SCOPE,
                                     "2026-06-01T00:00:00Z", "2026-06-30T00:00:00Z")
    assert again == {"ingested": 0, "skipped": 1}
    assert len(await sn.list(f"{SCOPE}_meeting")) == 1


@pytest.mark.asyncio
async def test_ingest_events_unmatched_attendees_still_retained_without_client():
    sn = FakeServiceNow()
    await _seed_client(sn)
    evt = {**EVT, "id": "evt-2",
           "attendees": [{"emailAddress": {"address": "x@unknown.com"}}]}
    graph = FakeGraph(events=[evt])
    res = await m365.ingest_events(graph, sn, SCOPE,
                                   "2026-06-01T00:00:00Z", "2026-06-30T00:00:00Z")
    assert res == {"ingested": 1, "skipped": 0}
    assert "client" not in (await sn.list(f"{SCOPE}_meeting"))[0]
