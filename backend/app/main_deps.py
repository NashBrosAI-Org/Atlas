import httpx
from app.config import get_settings, Settings
from app.servicenow import FakeServiceNow, HttpServiceNow, ServiceNowClient
from app.auth import TokenManager

_settings = get_settings()
_fake = FakeServiceNow()
_live: ServiceNowClient | None = None


def build_live_client(
    settings: Settings, transport: httpx.AsyncBaseTransport | None = None
) -> HttpServiceNow:
    """Construct the real SN Table API client from settings.

    Basic auth is the default (the live nnash path — D11): the instance walls
    the inbound-OAuth endpoints, so we authenticate as a local user with
    sn_username/sn_password. The oauth path keeps the legacy TokenManager
    Bearer flow for non-walled instances. `transport` is an httpx-native test
    seam; production passes none.
    """
    kwargs: dict = {"base_url": settings.sn_instance_url}
    if transport is not None:
        kwargs["transport"] = transport
    if settings.sn_auth_type == "basic":
        http = httpx.AsyncClient(
            auth=httpx.BasicAuth(settings.sn_username, settings.sn_password), **kwargs
        )
        return HttpServiceNow(http)
    http = httpx.AsyncClient(**kwargs)
    return HttpServiceNow(http, token_provider=TokenManager(settings).get_token)


def get_sn() -> ServiceNowClient:
    """Single DI seam for ServiceNow access. Returns a process-wide singleton
    in both modes so the live client's httpx connection pool (and any token
    cache) survive across requests."""
    global _live
    if _settings.use_fake:
        return _fake
    if _live is None:
        _live = build_live_client(_settings)
    return _live
