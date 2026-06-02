import httpx
from app.config import get_settings
from app.servicenow import FakeServiceNow, HttpServiceNow, ServiceNowClient
from app.auth import TokenManager

_settings = get_settings()
_fake = FakeServiceNow()


def get_sn() -> ServiceNowClient:
    if _settings.use_fake:
        return _fake
    http = httpx.AsyncClient(base_url=_settings.sn_instance_url)
    tokens = TokenManager(_settings)
    return HttpServiceNow(http, token_provider=tokens.get_token)
