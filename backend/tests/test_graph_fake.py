import pytest
from app.graph import FakeGraph

MSG = {"id": "m1", "subject": "Hi", "receivedDateTime": "2026-06-04T09:00:00Z",
       "from": {"emailAddress": {"address": "jane@acme.com", "name": "Jane"}}}


@pytest.mark.asyncio
async def test_list_messages_returns_seeded_and_filters_by_since():
    g = FakeGraph(messages=[
        MSG,
        {"id": "m0", "subject": "Old", "receivedDateTime": "2026-05-01T00:00:00Z"},
    ])
    assert {m["id"] for m in await g.list_messages()} == {"m1", "m0"}
    recent = await g.list_messages(since="2026-06-01T00:00:00Z")
    assert [m["id"] for m in recent] == ["m1"]


@pytest.mark.asyncio
async def test_list_events_filters_by_window():
    g = FakeGraph(events=[
        {"id": "e1", "subject": "QBR", "start": {"dateTime": "2026-06-05T15:00:00Z"}},
        {"id": "e0", "subject": "Past", "start": {"dateTime": "2026-01-01T00:00:00Z"}},
    ])
    win = await g.list_events("2026-06-01T00:00:00Z", "2026-06-30T00:00:00Z")
    assert [e["id"] for e in win] == ["e1"]
