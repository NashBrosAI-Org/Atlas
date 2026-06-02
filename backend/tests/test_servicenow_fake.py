import pytest
from app.servicenow import FakeServiceNow


@pytest.mark.asyncio
async def test_create_and_get():
    sn = FakeServiceNow()
    created = await sn.create("task", {"title": "A", "priority": "high"})
    assert created["sys_id"]
    got = await sn.get("task", created["sys_id"])
    assert got["title"] == "A"


@pytest.mark.asyncio
async def test_list_filters_by_query():
    sn = FakeServiceNow()
    await sn.create("task", {"title": "A", "client": "c1"})
    await sn.create("task", {"title": "B", "client": "c2"})
    rows = await sn.list("task", query={"client": "c1"})
    assert [r["title"] for r in rows] == ["A"]


@pytest.mark.asyncio
async def test_update_merges_fields():
    sn = FakeServiceNow()
    c = await sn.create("task", {"title": "A", "status": "open"})
    updated = await sn.update("task", c["sys_id"], {"status": "done"})
    assert updated["status"] == "done"
    assert updated["title"] == "A"
