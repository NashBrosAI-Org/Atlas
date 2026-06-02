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
async def test_create_posts_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(201, json={"result": {"sys_id": "9", "title": "New"}})

    sn = _client(handler)
    created = await sn.create("task", {"title": "New"})
    assert created["sys_id"] == "9"
