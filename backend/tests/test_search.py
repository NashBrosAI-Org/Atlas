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


@pytest.mark.asyncio
async def test_ranking_orders_exact_prefix_contains():
    sn = FakeServiceNow()
    await sn.create(f"{SCOPE}_client", {"name": "The Acme Holdings"})  # contains
    await sn.create(f"{SCOPE}_client", {"name": "Acme"})               # exact
    await sn.create(f"{SCOPE}_client", {"name": "Acme Corp"})          # prefix
    hits = await search.search(sn, SCOPE, "acme", types=["client"])
    assert [h["label"] for h in hits] == ["Acme", "Acme Corp", "The Acme Holdings"]


@pytest.mark.asyncio
async def test_body_match_carries_snippet():
    sn = FakeServiceNow()
    await sn.create(f"{SCOPE}_note", {"title": "Q3 plan", "body": "renewal for Acme due soon",
                                      "target_table": "client", "target_id": "c1"})
    hits = await search.search(sn, SCOPE, "acme", types=["note"])
    assert len(hits) == 1
    assert ">>Acme<<" in hits[0]["snippet"]
    assert hits[0]["score"] == search.BODY


@pytest.mark.asyncio
async def test_title_match_has_no_snippet():
    sn = FakeServiceNow()
    await sn.create(f"{SCOPE}_client", {"name": "Acme Corp"})
    hits = await search.search(sn, SCOPE, "acme", types=["client"])
    assert hits[0]["snippet"] is None


@pytest.mark.asyncio
async def test_new_types_are_searchable_by_default():
    sn = FakeServiceNow()
    await sn.create(f"{SCOPE}_meeting", {"title": "Acme sync"})
    await sn.create(f"{SCOPE}_theme", {"name": "Acme expansion"})
    await sn.create(f"{SCOPE}_key_date", {"title": "Acme renewal date"})
    await sn.create(f"{SCOPE}_link", {"title": "Acme portal"})
    types = {h["type"] for h in await search.search(sn, SCOPE, "acme")}
    assert {"meeting", "theme", "key_date", "link"} <= types


@pytest.mark.asyncio
async def test_transcripts_excluded_by_default_included_on_request():
    sn = FakeServiceNow()
    await sn.create(f"{SCOPE}_transcript", {"full_text": "we discussed acme renewal"})
    assert await search.search(sn, SCOPE, "acme") == []
    incl = await search.search(sn, SCOPE, "acme", types=["transcript"])
    assert len(incl) == 1 and incl[0]["type"] == "transcript"
    assert incl[0]["label"] == "Transcript"
    assert ">>acme<<" in incl[0]["snippet"]


@pytest.mark.asyncio
async def test_types_filter_restricts_scope():
    sn = FakeServiceNow()
    cid = (await sn.create(f"{SCOPE}_client", {"name": "Acme"}))["sys_id"]
    await sn.create(f"{SCOPE}_task", {"title": "Acme task", "client": cid})
    hits = await search.search(sn, SCOPE, "acme", types=["task"])
    assert {h["type"] for h in hits} == {"task"}
