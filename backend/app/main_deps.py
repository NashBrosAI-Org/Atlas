import httpx
from app.config import get_settings
from app.servicenow import FakeServiceNow, HttpServiceNow, ServiceNowClient
from app.auth import TokenManager

_settings = get_settings()
_fake = FakeServiceNow()
_live: ServiceNowClient | None = None


def get_sn() -> ServiceNowClient:
    """Single DI seam for ServiceNow access. Returns a process-wide singleton
    in both modes so the live client's httpx connection pool and the
    TokenManager's in-memory access-token cache survive across requests."""
    global _live
    if _settings.use_fake:
        return _fake
    if _live is None:
        http = httpx.AsyncClient(base_url=_settings.sn_instance_url)
        tokens = TokenManager(_settings)
        _live = HttpServiceNow(http, token_provider=tokens.get_token)
    return _live
