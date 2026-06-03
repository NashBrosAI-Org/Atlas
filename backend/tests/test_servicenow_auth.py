import httpx
import pytest

from app.servicenow import HttpServiceNow


class _CaptureTransport(httpx.AsyncBaseTransport):
    def __init__(self):
        self.last_request = None

    async def handle_async_request(self, request):
        self.last_request = request
        return httpx.Response(200, json={"result": []})


@pytest.mark.asyncio
async def test_bearer_header_when_token_provider_given():
    t = _CaptureTransport()
    client = httpx.AsyncClient(base_url="https://x", transport=t)
    sn = HttpServiceNow(client, token_provider=lambda: "abc")
    await sn.list("incident")
    assert t.last_request.headers["authorization"] == "Bearer abc"


@pytest.mark.asyncio
async def test_no_bearer_when_token_provider_none():
    t = _CaptureTransport()
    client = httpx.AsyncClient(base_url="https://x", transport=t, auth=("u", "p"))
    sn = HttpServiceNow(client, token_provider=None)
    await sn.list("incident")
    auth = t.last_request.headers["authorization"]
    assert auth.startswith("Basic ")
