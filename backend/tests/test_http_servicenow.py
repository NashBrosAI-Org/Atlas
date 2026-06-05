import httpx
import pytest
from app.servicenow import HttpServiceNow


def _client(handler) -> HttpServiceNow:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url="https://x.service-now.com")
    return HttpServiceNow(http, token_provider=lambda: "tok")


@pytest.mark.asyncio
async def test_list_builds_sysparm_query():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"result": [{"sys_id": "1", "title": "A"}]})

    sn = _client(handler)
    rows = await sn.list("task", query={"client": "c1", "status": "open"})
    assert rows == [{"sys_id": "1", "title": "A"}]
    assert "sysparm_query=client%3Dc1%5Estatus%3Dopen" in seen["url"]
    assert seen["auth"] == "Bearer tok"


@pytest.mark.asyncio
async def test_list_pages_through_limit_offset(monkeypatch):
    monkeypatch.setattr(HttpServiceNow, "_PAGE_SIZE", 2)
    calls, urls = [], []

    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params.get("sysparm_offset", "0"))
        calls.append(offset)
        urls.append(str(request.url))
        # 3 rows total across pages of 2: [r0,r1], [r2], then stop on the short page.
        rows = [{"sys_id": str(i)} for i in (0, 1)] if offset == 0 else [{"sys_id": "2"}]
        return httpx.Response(200, json={"result": rows})

    sn = _client(handler)
    rows = await sn.list("transcript")
    assert [r["sys_id"] for r in rows] == ["0", "1", "2"]
    assert calls == [0, 2]                       # second page fetched at offset 2, then stopped
    assert "sysparm_limit=2" in urls[0]          # limit sent

@pytest.mark.asyncio
async def test_list_single_full_page_fetches_next_until_short(monkeypatch):
    monkeypatch.setattr(HttpServiceNow, "_PAGE_SIZE", 2)
    pages = {0: [{"sys_id": "0"}, {"sys_id": "1"}], 2: [{"sys_id": "2"}, {"sys_id": "3"}], 4: []}

    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params.get("sysparm_offset", "0"))
        return httpx.Response(200, json={"result": pages[offset]})

    sn = _client(handler)
    rows = await sn.list("email")
    assert [r["sys_id"] for r in rows] == ["0", "1", "2", "3"]  # full page → fetch again → empty stops


@pytest.mark.asyncio
async def test_create_posts_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(201, json={"result": {"sys_id": "9", "title": "New"}})

    sn = _client(handler)
    created = await sn.create("task", {"title": "New"})
    assert created["sys_id"] == "9"


@pytest.mark.asyncio
async def test_get_returns_record():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/now/table/task/9"
        return httpx.Response(200, json={"result": {"sys_id": "9", "title": "X"}})

    sn = _client(handler)
    got = await sn.get("task", "9")
    assert got == {"sys_id": "9", "title": "X"}


@pytest.mark.asyncio
async def test_get_returns_none_on_404():
    sn = _client(lambda request: httpx.Response(404, json={"error": {"message": "not found"}}))
    assert await sn.get("task", "missing") is None


@pytest.mark.asyncio
async def test_update_patches_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/api/now/table/task/9"
        return httpx.Response(200, json={"result": {"sys_id": "9", "status": "done"}})

    sn = _client(handler)
    updated = await sn.update("task", "9", {"status": "done"})
    assert updated["status"] == "done"


@pytest.mark.asyncio
async def test_delete_sends_delete_request():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(204)

    sn = _client(handler)
    assert await sn.delete("task", "9") is True
    assert seen["method"] == "DELETE"
    assert seen["path"] == "/api/now/table/task/9"


@pytest.mark.asyncio
async def test_delete_returns_false_on_404():
    sn = _client(lambda request: httpx.Response(404, json={"error": {"message": "gone"}}))
    assert await sn.delete("task", "missing") is False


@pytest.mark.asyncio
@pytest.mark.parametrize("verb", ["get", "create", "update"])
async def test_reference_links_excluded_on_all_verbs(verb):
    """Real SN returns reference fields as {link,value} objects and choices/
    booleans as display values unless told otherwise. list already opts out;
    get/create/update must too, so live records match the fake's plain sys_id
    strings (the field-gap Task 15 warns about)."""
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"result": {"sys_id": "9"}})

    sn = _client(handler)
    if verb == "get":
        await sn.get("task", "9")
    elif verb == "create":
        await sn.create("task", {"title": "X"})
    else:
        await sn.update("task", "9", {"status": "done"})

    assert "sysparm_exclude_reference_link=true" in seen["url"]
    assert "sysparm_display_value=false" in seen["url"]
