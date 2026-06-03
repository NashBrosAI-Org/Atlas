import httpx

from app.config import get_settings
from app.servicenow import FakeServiceNow, HttpServiceNow, ServiceNowClient
from app.auth import TokenManager

_fake = FakeServiceNow()
_live: ServiceNowClient | None = None


def reset_sn() -> None:
    """Drop the cached live client so the next get_sn() rebuilds from current
    settings. Call after the user saves new connection settings."""
    global _live
    _live = None


def get_sn() -> ServiceNowClient:
    """Single DI seam for ServiceNow access. Returns the in-memory fake in demo
    mode, else a live client built from the current (possibly just-saved)
    settings. Basic auth (D11) is the default; OAuth uses the TokenManager."""
    global _live
    settings = get_settings()
    if settings.use_fake:
        return _fake
    if _live is None:
        if settings.sn_auth == "oauth":
            http = httpx.AsyncClient(base_url=settings.sn_instance_url)
            tokens = TokenManager(settings)
            _live = HttpServiceNow(http, token_provider=tokens.get_token)
        else:  # basic (default)
            http = httpx.AsyncClient(
                base_url=settings.sn_instance_url,
                auth=(settings.sn_oauth_username, settings.sn_oauth_password),
            )
            _live = HttpServiceNow(http, token_provider=None)
    return _live
