import httpx
import pytest
from app.config import Settings
from app.main_deps import build_live_client


@pytest.mark.asyncio
async def test_basic_auth_client_sends_basic_header():
    """Default live auth on nnash is basic (D11): the factory must build a
    client that authenticates with HTTP Basic using sn_username/sn_password."""
    settings = Settings(
        use_fake=False,
        sn_auth_type="basic",
        sn_instance_url="https://nnash.service-now.com",
        sn_username="atlas.sdk",
        sn_password="secret",
    )
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"result": []})

    sn = build_live_client(settings, transport=httpx.MockTransport(handler))
    await sn.list("x_atlas_sn_client")
    assert seen["auth"] == httpx.BasicAuth("atlas.sdk", "secret")._auth_header
