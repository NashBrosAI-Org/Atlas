import pytest
from app import search
from app.servicenow import FakeServiceNow

SCOPE = "x_atlas_sn"


@pytest.mark.asyncio
async def test_search_matches_across_types_and_is_case_insensitive():
    sn = FakeServiceNow()
    cid = (await sn.create(f"{SCOPE}_client", {"name": "Acme Corp", "email_domains": "acme.com"}))["sys_id"]
    await sn.create(f"{SCOPE}_task", {"title": "Acme renewal", "client": cid})
    await sn.create(f"{SCOPE}_contact", {"name": "Jane", "role_title": "VP", "client": cid})
    await sn.create(f"{SCOPE}_task", {"title": "Globex thing", "client": ""})

    hits = await search.search(sn, SCOPE, "acme")
    types = {h["type"] for h in hits}
    assert {"client", "task"} <= types
    assert all("acme" in (h["label"] + h["type"]).lower() or h["type"] == "client" for h in hits)
    # the task hit carries the owning client for navigation
    task_hit = next(h for h in hits if h["type"] == "task")
    assert task_hit["client"] == cid and task_hit["client_name"] == "Acme Corp"
    # case-insensitive + non-matching excluded
    assert any(h["label"] == "Acme renewal" for h in hits)
    assert not any("Globex" in h["label"] for h in hits)


@pytest.mark.asyncio
async def test_search_empty_query_returns_nothing():
    sn = FakeServiceNow()
    await sn.create(f"{SCOPE}_client", {"name": "Acme"})
    assert await search.search(sn, SCOPE, "  ") == []


@pytest.mark.asyncio
async def test_search_respects_limit():
    sn = FakeServiceNow()
    for i in range(10):
        await sn.create(f"{SCOPE}_task", {"title": f"match {i}"})
    assert len(await search.search(sn, SCOPE, "match", limit=5)) == 5
