from fastapi import APIRouter
from pydantic import BaseModel

import app.user_config as user_config
import app.main_deps as main_deps
from app.config import get_settings

router = APIRouter(prefix="/api")

# Non-secret settings the UI may read/write.
_NON_SECRET = ("use_fake", "sn_instance_url", "sn_scope", "sn_auth", "sn_oauth_username",
               "cooling_days", "stale_days", "m365_mail_filter")


class SettingsIn(BaseModel):
    use_fake: bool | None = None
    sn_instance_url: str | None = None
    sn_scope: str | None = None
    sn_auth: str | None = None
    sn_oauth_username: str | None = None
    cooling_days: int | None = None
    stale_days: int | None = None
    m365_mail_filter: str | None = None
    password: str | None = None  # write-only; never returned


@router.get("/settings")
def read_settings() -> dict:
    s = get_settings()
    out = {k: getattr(s, k) for k in _NON_SECRET}
    out["password_set"] = user_config.get_password() is not None
    return out


@router.put("/settings")
def write_settings(payload: SettingsIn) -> dict:
    values = {k: v for k, v in payload.model_dump(exclude_none=True).items() if k in _NON_SECRET}
    if values:
        user_config.save_config(values)
    if payload.password:
        user_config.save_password(payload.password)
    main_deps.reset_sn()  # next request uses the new settings
    return read_settings()


@router.get("/status")
def status() -> dict:
    s = get_settings()
    configured = (not s.use_fake) and bool(s.sn_instance_url) and bool(s.sn_oauth_username)
    return {"fake": s.use_fake, "configured": configured}


@router.post("/test-connection")
async def test_connection() -> dict:
    """Make one lightweight call through the current client. In demo mode this
    always succeeds; live, it surfaces auth/URL errors as ok=False + message."""
    try:
        # A single authenticated GET is enough to prove reachability + creds;
        # no query needed (the client's list() turns a dict into a sysparm_query).
        await main_deps.get_sn().list("sys_user")
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001 — report any failure to the UI
        return {"ok": False, "error": str(exc)}
