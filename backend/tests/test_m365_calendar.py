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
