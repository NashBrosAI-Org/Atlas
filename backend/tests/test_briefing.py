from datetime import date

import pytest

from app import briefing
from app.servicenow import FakeServiceNow

SCOPE = "x_atlas_sn"


@pytest.fixture
def sn() -> FakeServiceNow:
    return FakeServiceNow()


async def _client(sn, name="Acme", **extra):
    return (await sn.create(f"{SCOPE}_client", {"name": name, "status": "active", **extra}))["sys_id"]


@pytest.mark.asyncio
async def test_build_briefing_aggregates_day(sn):
    cid = await _client(sn, email_domains="acme.com")
    # tasks: a critical open, a low open, one done (excluded)
    await sn.create(f"{SCOPE}_task", {"title": "Crit", "client": cid, "priority": "critical", "status": "open"})
    await sn.create(f"{SCOPE}_task", {"title": "Low", "client": cid, "priority": "low", "status": "open"})
    await sn.create(f"{SCOPE}_task", {"title": "Done", "client": cid, "priority": "high", "status": "done"})
    # meetings: one today, one another day
    await sn.create(f"{SCOPE}_meeting", {"title": "Today QBR", "client": cid, "datetime": "2026-06-04T15:00:00Z"})
    await sn.create(f"{SCOPE}_meeting", {"title": "Next week", "client": cid, "datetime": "2026-06-11T15:00:00Z"})
    # a key date due in the window
    await sn.create(f"{SCOPE}_key_date", {"title": "Renewal", "date": "2026-06-07", "reminder_lead_days": "7", "client": cid})

    b = await briefing.build_briefing(sn, SCOPE, today=date(2026, 6, 4))

    assert b["date"] == "2026-06-04"
    # Now tasks: ordered (critical before low), done excluded
    assert [t["title"] for t in b["now_tasks"]] == ["Crit", "Low"]
    # Today's meetings only
    assert [m["title"] for m in b["todays_meetings"]] == ["Today QBR"]
    # Reminders include the renewal
    assert any(r["title"] == "Renewal" for r in b["reminders"])
    # Radar present (list)
    assert isinstance(b["radar"], list)


@pytest.mark.asyncio
async def test_now_tasks_respects_limit(sn):
    cid = await _client(sn)
    for i in range(7):
        await sn.create(f"{SCOPE}_task", {"title": f"t{i}", "client": cid, "priority": "medium", "status": "open"})
    b = await briefing.build_briefing(sn, SCOPE, today=date(2026, 6, 4), now_limit=5)
    assert len(b["now_tasks"]) == 5


@pytest.mark.asyncio
async def test_radar_flags_stale_client(sn):
    # An active client with no activity, created 45 days before "today" → stale.
    import datetime as _dt
    if hasattr(sn, "_clock"):
        sn._clock = lambda: _dt.datetime(2026, 4, 20, tzinfo=_dt.timezone.utc)
    await _client(sn, name="Stale Co")
    if hasattr(sn, "_clock"):
        sn._clock = lambda: _dt.datetime.now(_dt.timezone.utc)
    b = await briefing.build_briefing(sn, SCOPE, today=date(2026, 6, 4),
                                      cooling_days=14, stale_days=30)
    assert any(r["client_name"] == "Stale Co" and r["tier"] == "stale" for r in b["radar"])
