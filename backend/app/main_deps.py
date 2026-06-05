import httpx

from app.ai import AIClient, FakeAI
from app.config import get_settings
from app.graph import FakeGraph, GraphClient
from app.servicenow import FakeServiceNow, HttpServiceNow, ServiceNowClient
from app.auth import TokenManager

_fake = FakeServiceNow()
_live: ServiceNowClient | None = None
_fake_graph = FakeGraph()
_fake_ai = FakeAI()


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


def get_graph() -> GraphClient:
    """DI seam for Microsoft Graph. Returns the in-memory fake until Phase 4
    wires the live HttpGraph (work-Mac only, after the Entra recon GO)."""
    settings = get_settings()
    if settings.m365_use_fake:
        return _fake_graph
    raise RuntimeError("live Graph (HttpGraph) not wired yet — see P2 plan Phase 4")


def get_ai() -> AIClient:
    """DI seam for the AI client. Returns the deterministic fake until a later
    phase wires the live AnthropicAI (and only when an API key is configured)."""
    if get_settings().ai_use_fake:
        return _fake_ai
    raise RuntimeError("live AnthropicAI not wired yet — see P3 plan")
