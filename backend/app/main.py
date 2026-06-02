import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.servicenow import FakeServiceNow, HttpServiceNow, ServiceNowClient
from app.auth import TokenManager

app = FastAPI(title="Atlas")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_settings = get_settings()
_fake = FakeServiceNow()


def get_sn() -> ServiceNowClient:
    if _settings.use_fake:
        return _fake
    http = httpx.AsyncClient(base_url=_settings.sn_instance_url)
    tokens = TokenManager(_settings)
    return HttpServiceNow(http, token_provider=tokens.get_token)


@app.get("/api/health")
def health():
    return {"status": "ok"}


from app.routers import clients, tasks  # noqa: E402

app.include_router(clients.router)
app.include_router(tasks.router)
