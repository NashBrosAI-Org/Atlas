from datetime import datetime, timezone

import pytest

from app.servicenow import FakeServiceNow
from app.awareness import build_timeline, recent_activity, stale_radar

SCOPE = "x_test"


def _clock(seq):
    it = iter(seq)
    return lambda: next(it)


async def _seed(sn):
    c = await sn.create(f"{SCOPE}_client", {"name": "Acme", "status": "active"})
    cid = c["sys_id"]
    await sn.create(f"{SCOPE}_task", {"title": "T1", "client": cid, "status": "open"})
    await sn.create(f"{SCOPE}_meeting", {"title": "Kickoff", "client": cid,
                                         "datetime": "2026-05-01T10:00:00Z"})
    await sn.create(f"{SCOPE}_note", {"title": "N1", "note_type": "risk",
                                      "target_table": "client", "target_id": cid})
    return cid


@pytest.mark.asyncio
async def test_timeline_newest_first_and_domain_date_wins():
    times = [datetime(2026, 6, d, 9, 0, 0, tzinfo=timezone.utc) for d in (1, 2, 3, 4)]
    sn = FakeServiceNow(clock=_clock(times))
    cid = await _seed(sn)
    tl = await build_timeline(sn, SCOPE, cid)
    assert [e["type"] for e in tl][0] in {"task", "note"}
    meeting = next(e for e in tl if e["type"] == "meeting")
    assert meeting["when"] == "2026-05-01T10:00:00Z"
    whens = [e["when"] for e in tl]
    assert whens == sorted(whens, reverse=True)


@pytest.mark.asyncio
async def test_timeline_missing_client_returns_none():
    sn = FakeServiceNow()
    assert await build_timeline(sn, SCOPE, "nope") is None


@pytest.mark.asyncio
async def test_timeline_existing_client_no_activity_is_empty_list():
    sn = FakeServiceNow()
    c = await sn.create(f"{SCOPE}_client", {"name": "Empty", "status": "active"})
    assert await build_timeline(sn, SCOPE, c["sys_id"]) == []


@pytest.mark.asyncio
async def test_recent_activity_across_clients_newest_first():
    times = [datetime(2026, 6, d, 9, 0, 0, tzinfo=timezone.utc) for d in range(1, 10)]
    sn = FakeServiceNow(clock=_clock(times))
    a = await sn.create(f"{SCOPE}_client", {"name": "Acme", "status": "active"})
    b = await sn.create(f"{SCOPE}_client", {"name": "Globex", "status": "active"})
    await sn.create(f"{SCOPE}_task", {"title": "old", "client": a["sys_id"]})
    await sn.create(f"{SCOPE}_task", {"title": "new", "client": b["sys_id"]})
    feed = await recent_activity(sn, SCOPE)
    assert feed[0]["title"] == "Task: new"
    assert feed[0]["client_name"] == "Globex"
    assert {e["client_name"] for e in feed} == {"Acme", "Globex"}


@pytest.mark.asyncio
async def test_recent_activity_respects_limit():
    times = [datetime(2026, 6, 1, 9, m, 0, tzinfo=timezone.utc) for m in range(10)]
    sn = FakeServiceNow(clock=_clock(times))
    c = await sn.create(f"{SCOPE}_client", {"name": "Acme", "status": "active"})
    for i in range(5):
        await sn.create(f"{SCOPE}_task", {"title": f"t{i}", "client": c["sys_id"]})
    assert len(await recent_activity(sn, SCOPE, limit=3)) == 3


NOW = datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_radar_tiers_and_active_only():
    sn = FakeServiceNow(clock=lambda: datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc))
    fresh = await sn.create(f"{SCOPE}_client", {"name": "Fresh", "status": "active"})
    await sn.create(f"{SCOPE}_task", {"title": "x", "client": fresh["sys_id"]})
    sn._clock = lambda: datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
    cooling = await sn.create(f"{SCOPE}_client", {"name": "Cooling", "status": "active"})
    await sn.create(f"{SCOPE}_task", {"title": "y", "client": cooling["sys_id"]})
    sn._clock = lambda: datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
    stale = await sn.create(f"{SCOPE}_client", {"name": "Stale", "status": "active"})
    await sn.create(f"{SCOPE}_task", {"title": "z", "client": stale["sys_id"]})
    sn._clock = lambda: datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    await sn.create(f"{SCOPE}_client", {"name": "OldProspect", "status": "prospect"})

    radar = await stale_radar(sn, SCOPE, cooling_days=14, stale_days=30, now=NOW)
    by_name = {r["client_name"]: r for r in radar}
    assert "Fresh" not in by_name
    assert "OldProspect" not in by_name
    assert by_name["Cooling"]["tier"] == "cooling"
    assert by_name["Stale"]["tier"] == "stale"
    assert radar[0]["client_name"] == "Stale"


@pytest.mark.asyncio
async def test_radar_active_client_with_no_activity_uses_own_age():
    sn = FakeServiceNow(clock=lambda: datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc))
    await sn.create(f"{SCOPE}_client", {"name": "Ghost", "status": "active"})
    radar = await stale_radar(sn, SCOPE, cooling_days=14, stale_days=30, now=NOW)
    assert radar and radar[0]["client_name"] == "Ghost" and radar[0]["tier"] == "stale"
