from datetime import datetime, timezone

import pytest

from app.servicenow import FakeServiceNow


def _clock(values):
    it = iter(values)
    return lambda: next(it)


@pytest.mark.asyncio
async def test_create_stamps_created_and_updated():
    fixed = datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
    sn = FakeServiceNow(clock=lambda: fixed)
    rec = await sn.create("x_t", {"name": "a"})
    assert rec["sys_created_on"] == "2026-06-01T09:00:00Z"
    assert rec["sys_updated_on"] == "2026-06-01T09:00:00Z"


@pytest.mark.asyncio
async def test_update_refreshes_updated_only():
    t0 = datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 6, 2, 9, 0, 0, tzinfo=timezone.utc)
    sn = FakeServiceNow(clock=_clock([t0, t1]))
    rec = await sn.create("x_t", {"name": "a"})
    updated = await sn.update("x_t", rec["sys_id"], {"name": "b"})
    assert updated["sys_created_on"] == "2026-06-01T09:00:00Z"
    assert updated["sys_updated_on"] == "2026-06-02T09:00:00Z"


@pytest.mark.asyncio
async def test_default_clock_is_utc_now():
    sn = FakeServiceNow()
    rec = await sn.create("x_t", {"name": "a"})
    assert rec["sys_created_on"].endswith("Z") and "T" in rec["sys_created_on"]
