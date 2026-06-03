# Atlas In-App Configuration (Plan B) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a user configure Atlas entirely inside the app — a Settings/Integrations page where they enter their ServiceNow instance + credentials and toggle demo mode — with config persisted per-user (non-secrets in `~/Library/Application Support/Atlas/config.json`, the password in the macOS Keychain), no file editing, and a live "Test connection" against their instance.

**Architecture:** A new per-user config store (`backend/app/user_config.py` + `desktop/paths.py`) holds non-secret settings in `config.json` and the SN password in the Keychain (`keyring`, service `atlas-sn`). `get_settings()` overlays that store on top of the existing pydantic/`.env` defaults; `get_sn()` becomes dynamic so saved settings take effect without a restart. The ServiceNow client gains a **basic-auth** path (per decision D11 — `nnash` walls OAuth). New thin routes (`/api/settings`, `/api/status`, `/api/test-connection`) back a React Settings page that doubles as the first-run surface.

**Tech Stack:** FastAPI + pydantic v2, `keyring` (macOS Keychain), httpx basic auth, React/Vite, pytest + `TestClient` (monkeypatching `keyring` and an `ATLAS_DATA_DIR` temp override).

---

## CRITICAL design decision — basic auth, not OAuth (supersedes the spec)

The desktop-app spec (`docs/superpowers/specs/2026-06-02-atlas-desktop-app-design.md`) described an in-app **OAuth** connect flow with `/oauth/callback`. **Decision D11** (in `docs/PROGRESS.md`, made after that spec) found every OAuth path is walled on the `nnash` Zurich instance, and both the SDK and the live FastAPI backend must use **basic auth** via a local non-MFA user. Therefore this plan implements basic auth:

- The Settings page captures **instance URL + username + password** (+ scope, + demo toggle).
- The password is the only secret → macOS Keychain. The rest → `config.json`.
- The SN client sends an HTTP **Basic** `Authorization` header (httpx `auth=(user, pass)`), not Bearer.
- `auth.py`'s OAuth `TokenManager` is left in place (unused by this flow) for a possible future instance that supports OAuth; this plan does not delete it.

If you (the human) want OAuth instead, stop and say so before execution — it changes Tasks 4–7.

---

## Scope boundaries
- **In scope:** per-user config storage; settings/status/test-connection API; basic-auth client path; dynamic `get_sn`; React Settings page + first-run + "Try with demo data" toggle.
- **Out of scope (later):** M365/email connect (P2); the shareable `install.sh` + in-app setup instructions + R5 (Plan C); OAuth; app `.icns` icon; seeding `FakeServiceNow` with demo records (optional nicety — may be added in Task 7 if trivial).
- **Suggested execution split if you want smaller PRs:** **B1** = Tasks 1–3, 6 (config store + settings/status API + Settings UI for non-secrets + demo toggle) — independently shippable; **B2** = Tasks 4–5, 7 (basic-auth client + dynamic `get_sn` + password/Keychain + Test connection). This single plan covers both.

**Assumed working dir:** the worktree root `/Users/nick/Atlas/.claude/worktrees/desktop-app` (`$REPO`). Backend venv at `$REPO/backend/.venv` (Python 3.14 — fine for the app; the *packaging* venv in Plan A needs 3.10–3.13 but that's not used here). Run backend tests from `$REPO/backend` via `./.venv/bin/python -m pytest`; desktop tests from `$REPO` via `./backend/.venv/bin/python -m pytest desktop/tests`.

---

## File structure

| File | New/Mod | Responsibility |
|---|---|---|
| `desktop/paths.py` | Create | `user_data_dir()` / `config_file()` — per-user dir (`~/Library/Application Support/Atlas`), honoring `ATLAS_DATA_DIR` override |
| `desktop/tests/test_paths.py` | Create | Tests for the override + default path + config_file location |
| `backend/app/user_config.py` | Create | Read/write `config.json` (non-secret) + Keychain password; `load_overlay()`, `save_config()`, `save_password()`, `get_password()`, `clear_password()` |
| `backend/tests/test_user_config.py` | Create | Round-trip config.json + Keychain (monkeypatched), missing-file defaults |
| `backend/app/config.py` | Modify | `get_settings()` overlays `user_config` on top of env/`.env`; add `sn_auth` field default `"basic"` |
| `backend/tests/test_config_overlay.py` | Create | Saved config.json + Keychain password surface in `get_settings()`; fallback when absent |
| `backend/app/servicenow.py` | Modify | `HttpServiceNow`: make Bearer optional (basic auth supplied at the httpx client level) |
| `backend/tests/test_servicenow_auth.py` | Create | Bearer header present iff a token provider is given; absent for basic mode |
| `backend/app/main_deps.py` | Modify | `get_sn()` reads current settings, builds Fake/basic-auth client, rebuilds on config change; `reset_sn()` to invalidate |
| `backend/tests/test_main_deps.py` | Create | Fake when `use_fake`; basic-auth `HttpServiceNow` when configured; `reset_sn()` picks up new settings |
| `backend/app/routers/settings.py` | Create | `GET/PUT /api/settings`, `GET /api/status`, `POST /api/test-connection` |
| `backend/tests/test_settings_api.py` | Create | Tests for all four endpoints against FakeServiceNow + temp dir + fake keyring |
| `backend/app/main.py` | Modify | Include the settings router (before `mount_frontend`) |
| `frontend/src/types.ts` | Modify | Add `AppSettings`, `AppStatus`, `TestResult` types |
| `frontend/src/api.ts` | Modify | Add `getSettings`, `saveSettings`, `getStatus`, `testConnection` |
| `frontend/src/SettingsView.tsx` | Create | The Settings/Integrations form (instance/user/password/scope/demo + Save + Test + status) |
| `frontend/src/App.tsx` | Modify | Add a Settings route/tab; on first run (not configured, not demo) land on Settings |
| `docs/PROGRESS.md` | Modify | Record Plan B (decision **D14**) |

---

## Task 0: Baseline

- [ ] **Step 1:** `cd "$REPO/backend" && ./.venv/bin/python -m pytest -q` → all pass (Plan A left 36 green). If red, STOP.
- [ ] **Step 2:** `cd "$REPO" && ./backend/.venv/bin/python -m pytest desktop/tests -q` → 3 pass.

---

## Task 1: Per-user paths

**Files:** Create `desktop/paths.py`, `desktop/tests/test_paths.py`

- [ ] **Step 1: Write the failing test** — `desktop/tests/test_paths.py`:
```python
from pathlib import Path

from desktop.paths import user_data_dir, config_file


def test_user_data_dir_default(monkeypatch):
    monkeypatch.delenv("ATLAS_DATA_DIR", raising=False)
    p = user_data_dir()
    assert p == Path.home() / "Library" / "Application Support" / "Atlas"


def test_user_data_dir_honors_override(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    assert user_data_dir() == tmp_path


def test_config_file_under_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    assert config_file() == tmp_path / "config.json"
```

- [ ] **Step 2:** Run → FAIL (`No module named 'desktop.paths'`):
`cd "$REPO" && ./backend/.venv/bin/python -m pytest desktop/tests/test_paths.py -q`

- [ ] **Step 3: Implement** — `desktop/paths.py`:
```python
"""Per-user filesystem locations for Atlas (writable, outside the read-only app
bundle). Override the base dir with ATLAS_DATA_DIR (used by tests)."""
from __future__ import annotations

import os
from pathlib import Path


def user_data_dir() -> Path:
    override = os.environ.get("ATLAS_DATA_DIR")
    if override:
        return Path(override)
    return Path.home() / "Library" / "Application Support" / "Atlas"


def config_file() -> Path:
    return user_data_dir() / "config.json"
```

- [ ] **Step 4:** Run → PASS (3).
- [ ] **Step 5: Commit**
```bash
cd "$REPO" && git add desktop/paths.py desktop/tests/test_paths.py
git commit -m "feat: per-user data dir + config_file path helpers"
```

---

## Task 2: Config store (config.json + Keychain)

**Files:** Create `backend/app/user_config.py`, `backend/tests/test_user_config.py`

**Note on imports:** `user_config.py` lives in the backend (`app` package) but reads the path from `desktop.paths`. To avoid a backend→desktop import coupling, `paths` resolution is injected: `user_config` accepts an explicit path or falls back to `ATLAS_DATA_DIR`/default computed locally (duplicate the tiny path logic rather than import `desktop`). This keeps the backend importable without the `desktop` package on the path (e.g. in CI running only `backend/`).

- [ ] **Step 1: Write the failing test** — `backend/tests/test_user_config.py`:
```python
import json
from pathlib import Path

import app.user_config as uc


def test_load_overlay_empty_when_no_file(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    assert uc.load_overlay() == {}


def test_save_and_load_config_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    uc.save_config({"sn_instance_url": "https://x.service-now.com", "use_fake": False})
    overlay = uc.load_overlay()
    assert overlay["sn_instance_url"] == "https://x.service-now.com"
    assert overlay["use_fake"] is False
    assert json.loads((tmp_path / "config.json").read_text())["use_fake"] is False


def test_password_roundtrip_via_keychain(monkeypatch):
    store = {}
    monkeypatch.setattr(uc.keyring, "set_password", lambda s, k, v: store.__setitem__((s, k), v))
    monkeypatch.setattr(uc.keyring, "get_password", lambda s, k: store.get((s, k)))
    monkeypatch.setattr(uc.keyring, "delete_password", lambda s, k: store.pop((s, k), None))
    uc.save_password("hunter2")
    assert uc.get_password() == "hunter2"
    uc.clear_password()
    assert uc.get_password() is None
```

- [ ] **Step 2:** Run → FAIL (`No module named 'app.user_config'`):
`cd "$REPO/backend" && ./.venv/bin/python -m pytest tests/test_user_config.py -q`

- [ ] **Step 3: Implement** — `backend/app/user_config.py`:
```python
"""Per-user persistence: non-secret settings in config.json, the SN password in
the macOS Keychain. Mirrors the small path logic from desktop/paths.py so the
backend has no import dependency on the desktop package."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

import keyring

_KEYRING_SERVICE = "atlas-sn"
_PASSWORD_KEY = "sn_password"


def _data_dir() -> Path:
    override = os.environ.get("ATLAS_DATA_DIR")
    if override:
        return Path(override)
    return Path.home() / "Library" / "Application Support" / "Atlas"


def _config_file() -> Path:
    return _data_dir() / "config.json"


def load_overlay() -> dict[str, Any]:
    """Non-secret settings the user saved, or {} if none yet."""
    path = _config_file()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(values: dict[str, Any]) -> None:
    """Merge ``values`` into config.json (creating the dir/file as needed)."""
    path = _config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    current = load_overlay()
    current.update(values)
    path.write_text(json.dumps(current, indent=2))


def save_password(password: str) -> None:
    keyring.set_password(_KEYRING_SERVICE, _PASSWORD_KEY, password)


def get_password() -> Optional[str]:
    return keyring.get_password(_KEYRING_SERVICE, _PASSWORD_KEY)


def clear_password() -> None:
    try:
        keyring.delete_password(_KEYRING_SERVICE, _PASSWORD_KEY)
    except keyring.errors.PasswordDeleteError:
        pass
```

- [ ] **Step 4:** Run → PASS (3).
- [ ] **Step 5: Commit**
```bash
cd "$REPO" && git add backend/app/user_config.py backend/tests/test_user_config.py
git commit -m "feat: per-user config store (config.json + Keychain password)"
```

---

## Task 3: Overlay user config onto Settings

**Files:** Modify `backend/app/config.py`, Create `backend/tests/test_config_overlay.py`

- [ ] **Step 1: Write the failing test** — `backend/tests/test_config_overlay.py`:
```python
import app.user_config as uc
from app.config import get_settings


def test_defaults_when_no_overlay(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(uc, "get_password", lambda: None)
    s = get_settings()
    assert s.use_fake is True  # default


def test_overlay_and_password_applied(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    uc.save_config({
        "use_fake": False,
        "sn_instance_url": "https://nnash.service-now.com",
        "sn_oauth_username": "atlas.sdk",
    })
    monkeypatch.setattr(uc, "get_password", lambda: "secret-pw")
    s = get_settings()
    assert s.use_fake is False
    assert s.sn_instance_url == "https://nnash.service-now.com"
    assert s.sn_oauth_username == "atlas.sdk"
    assert s.sn_oauth_password == "secret-pw"
```

- [ ] **Step 2:** Run → FAIL (assertions: overlay not applied):
`cd "$REPO/backend" && ./.venv/bin/python -m pytest tests/test_config_overlay.py -q`

- [ ] **Step 3: Implement** — edit `backend/app/config.py`. Add `sn_auth` field and rewrite `get_settings()`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

import app.user_config as user_config


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    use_fake: bool = True
    sn_instance_url: str = "https://example.service-now.com"
    sn_scope: str = "x_vendor_atlas"
    sn_auth: str = "basic"  # "basic" (D11) or "oauth"
    sn_oauth_client_id: str = ""
    sn_oauth_client_secret: str = ""
    sn_oauth_username: str = ""
    sn_oauth_password: str = ""


def get_settings() -> Settings:
    """Env/.env defaults, overlaid with the user's saved config.json and the
    Keychain password (so in-app Settings take effect without code changes)."""
    overlay = user_config.load_overlay()
    base = Settings()
    merged = base.model_dump()
    merged.update({k: v for k, v in overlay.items() if k in merged})
    settings = Settings(**merged)
    pw = user_config.get_password()
    if pw is not None:
        settings.sn_oauth_password = pw
    return settings
```

- [ ] **Step 4:** Run → PASS (2). Then full suite: `cd "$REPO/backend" && ./.venv/bin/python -m pytest -q` → all pass.
- [ ] **Step 5: Commit**
```bash
cd "$REPO" && git add backend/app/config.py backend/tests/test_config_overlay.py
git commit -m "feat: overlay per-user config.json + Keychain password onto Settings"
```

---

## Task 4: Basic-auth path in the SN client

**Files:** Modify `backend/app/servicenow.py`, Create `backend/tests/test_servicenow_auth.py`

- [ ] **Step 1: Write the failing test** — `backend/tests/test_servicenow_auth.py`:
```python
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
    # Basic auth is applied at the client level (httpx auth=...).
    client = httpx.AsyncClient(base_url="https://x", transport=t, auth=("u", "p"))
    sn = HttpServiceNow(client, token_provider=None)
    await sn.list("incident")
    auth = t.last_request.headers["authorization"]
    assert auth.startswith("Basic ")
```

- [ ] **Step 2:** Run → FAIL (current `_headers()` always sends Bearer / crashes on `None()`):
`cd "$REPO/backend" && ./.venv/bin/python -m pytest tests/test_servicenow_auth.py -q`

- [ ] **Step 3: Implement** — in `backend/app/servicenow.py`, change `HttpServiceNow.__init__` and `_headers`:
```python
    def __init__(self, http: httpx.AsyncClient, token_provider: Optional[Callable[[], str]] = None) -> None:
        self._http = http
        self._token = token_provider

    def _headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self._token is not None:
            headers["Authorization"] = f"Bearer {self._token()}"
        return headers
```
(Everything else in `HttpServiceNow` is unchanged; basic-auth credentials ride on the `httpx.AsyncClient(auth=...)` passed in by `main_deps`.)

- [ ] **Step 4:** Run → PASS (2). Full suite green.
- [ ] **Step 5: Commit**
```bash
cd "$REPO" && git add backend/app/servicenow.py backend/tests/test_servicenow_auth.py
git commit -m "feat: HttpServiceNow supports basic auth (optional Bearer token provider)"
```

---

## Task 5: Dynamic `get_sn` (picks up saved settings, basic auth)

**Files:** Modify `backend/app/main_deps.py`, Create `backend/tests/test_main_deps.py`

- [ ] **Step 1: Write the failing test** — `backend/tests/test_main_deps.py`:
```python
import app.user_config as uc
import app.main_deps as deps
from app.servicenow import FakeServiceNow, HttpServiceNow


def test_returns_fake_when_use_fake(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(uc, "get_password", lambda: None)
    deps.reset_sn()
    assert isinstance(deps.get_sn(), FakeServiceNow)


def test_returns_basic_auth_http_when_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    uc.save_config({
        "use_fake": False,
        "sn_instance_url": "https://nnash.service-now.com",
        "sn_oauth_username": "atlas.sdk",
    })
    monkeypatch.setattr(uc, "get_password", lambda: "pw")
    deps.reset_sn()
    client = deps.get_sn()
    assert isinstance(client, HttpServiceNow)


def test_reset_sn_picks_up_new_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(uc, "get_password", lambda: None)
    deps.reset_sn()
    assert isinstance(deps.get_sn(), FakeServiceNow)
    uc.save_config({"use_fake": False, "sn_instance_url": "https://nnash.service-now.com",
                    "sn_oauth_username": "u"})
    monkeypatch.setattr(uc, "get_password", lambda: "pw")
    deps.reset_sn()
    assert isinstance(deps.get_sn(), HttpServiceNow)
```

- [ ] **Step 2:** Run → FAIL (`reset_sn` missing; `get_sn` caches import-time settings):
`cd "$REPO/backend" && ./.venv/bin/python -m pytest tests/test_main_deps.py -q`

- [ ] **Step 3: Implement** — replace `backend/app/main_deps.py`:
```python
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
```

- [ ] **Step 4:** Run → PASS (3). Full suite green.
- [ ] **Step 5: Commit**
```bash
cd "$REPO" && git add backend/app/main_deps.py backend/tests/test_main_deps.py
git commit -m "feat: dynamic get_sn with basic-auth live client + reset_sn"
```

---

## Task 6: Settings / status / test-connection API

**Files:** Create `backend/app/routers/settings.py`, `backend/tests/test_settings_api.py`; Modify `backend/app/main.py`

- [ ] **Step 1: Write the failing test** — `backend/tests/test_settings_api.py`:
```python
from fastapi.testclient import TestClient

import app.user_config as uc
import app.main_deps as deps
from app.main import app


def _client(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    store = {}
    monkeypatch.setattr(uc.keyring, "set_password", lambda s, k, v: store.__setitem__((s, k), v))
    monkeypatch.setattr(uc.keyring, "get_password", lambda s, k: store.get((s, k)))
    monkeypatch.setattr(uc.keyring, "delete_password", lambda s, k: store.pop((s, k), None))
    deps.reset_sn()
    return TestClient(app)


def test_status_starts_unconfigured_in_demo(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    r = c.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert body["fake"] is True
    assert body["configured"] is False


def test_get_settings_hides_password_but_reports_presence(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    r = c.get("/api/settings")
    assert r.status_code == 200
    body = r.json()
    assert "sn_oauth_password" not in body
    assert body["password_set"] is False
    assert body["use_fake"] is True


def test_put_settings_persists_nonsecret_and_password(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    r = c.put("/api/settings", json={
        "use_fake": False,
        "sn_instance_url": "https://nnash.service-now.com",
        "sn_oauth_username": "atlas.sdk",
        "sn_scope": "x_atlas_sn",
        "password": "hunter2",
    })
    assert r.status_code == 200
    assert uc.load_overlay()["sn_instance_url"] == "https://nnash.service-now.com"
    assert uc.get_password() == "hunter2"
    got = c.get("/api/settings").json()
    assert got["password_set"] is True
    assert got["use_fake"] is False


def test_put_settings_without_password_keeps_existing(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    c.put("/api/settings", json={"use_fake": False, "sn_instance_url": "https://x",
                                 "sn_oauth_username": "u", "password": "pw1"})
    c.put("/api/settings", json={"use_fake": False, "sn_instance_url": "https://y",
                                 "sn_oauth_username": "u"})  # no password field
    assert uc.get_password() == "pw1"  # unchanged
    assert uc.load_overlay()["sn_instance_url"] == "https://y"


def test_test_connection_ok_in_demo(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    r = c.post("/api/test-connection")
    assert r.status_code == 200
    assert r.json()["ok"] is True
```

- [ ] **Step 2:** Run → FAIL (`/api/settings` etc. 404):
`cd "$REPO/backend" && ./.venv/bin/python -m pytest tests/test_settings_api.py -q`

- [ ] **Step 3: Implement** — `backend/app/routers/settings.py`:
```python
from fastapi import APIRouter
from pydantic import BaseModel

import app.user_config as user_config
import app.main_deps as main_deps
from app.config import get_settings

router = APIRouter(prefix="/api")

# Non-secret settings the UI may read/write.
_NON_SECRET = ("use_fake", "sn_instance_url", "sn_scope", "sn_auth", "sn_oauth_username")


class SettingsIn(BaseModel):
    use_fake: bool | None = None
    sn_instance_url: str | None = None
    sn_scope: str | None = None
    sn_auth: str | None = None
    sn_oauth_username: str | None = None
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
        await main_deps.get_sn().list("sys_user", {"sysparm_limit": "1"})
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001 — report any failure to the UI
        return {"ok": False, "error": str(exc)}
```

- [ ] **Step 4: Wire the router** — in `backend/app/main.py`, add with the other router imports/includes (BEFORE the `mount_frontend(app, _dist)` call at the bottom):
```python
from app.routers import settings as settings_router  # noqa: E402
app.include_router(settings_router.router)
```

- [ ] **Step 5:** Run → PASS (6). Full suite green.
- [ ] **Step 6: Commit**
```bash
cd "$REPO" && git add backend/app/routers/settings.py backend/tests/test_settings_api.py backend/app/main.py
git commit -m "feat: /api/settings, /api/status, /api/test-connection"
```

---

## Task 7: React Settings page + first-run + demo toggle

**Files:** Modify `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/App.tsx`; Create `frontend/src/SettingsView.tsx`

- [ ] **Step 1: Add types** — append to `frontend/src/types.ts`:
```ts
export interface AppSettings {
  use_fake: boolean;
  sn_instance_url: string;
  sn_scope: string;
  sn_auth: string;
  sn_oauth_username: string;
  password_set: boolean;
}
export interface AppStatus {
  fake: boolean;
  configured: boolean;
}
export interface TestResult {
  ok: boolean;
  error?: string;
}
```

- [ ] **Step 2: Add API calls** — append to `frontend/src/api.ts` (uses the existing `http`/`jsonBody` helpers):
```ts
import type { AppSettings, AppStatus, TestResult } from "./types";

export async function getStatus(): Promise<AppStatus> {
  return http<AppStatus>("/status");
}
export async function getSettings(): Promise<AppSettings> {
  return http<AppSettings>("/settings");
}
export async function saveSettings(s: Partial<AppSettings> & { password?: string }): Promise<AppSettings> {
  return http<AppSettings>("/settings", jsonBody("PUT", s));
}
export async function testConnection(): Promise<TestResult> {
  return http<TestResult>("/test-connection", { method: "POST" });
}
```
(Adjust the top `import type { ... }` line in `api.ts` to also include `AppSettings, AppStatus, TestResult`, OR keep the separate import statement above — both compile.)

- [ ] **Step 3: Create `frontend/src/SettingsView.tsx`:**
```tsx
import { useEffect, useState } from "react";
import { getSettings, saveSettings, testConnection } from "./api";
import type { AppSettings, TestResult } from "./types";

export function SettingsView({ onSaved }: { onSaved?: () => void }) {
  const [s, setS] = useState<AppSettings | null>(null);
  const [password, setPassword] = useState("");
  const [test, setTest] = useState<TestResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    getSettings().then(setS).catch((e) => setMsg(String(e)));
  }, []);

  if (!s) return <div className="settings">Loading settings…</div>;

  const set = (patch: Partial<AppSettings>) => setS({ ...s, ...patch });

  async function save() {
    setBusy(true);
    setMsg("");
    try {
      const saved = await saveSettings({
        use_fake: s.use_fake,
        sn_instance_url: s.sn_instance_url,
        sn_scope: s.sn_scope,
        sn_oauth_username: s.sn_oauth_username,
        ...(password ? { password } : {}),
      });
      setS(saved);
      setPassword("");
      setMsg("Saved.");
      onSaved?.();
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function runTest() {
    setBusy(true);
    setTest(null);
    try {
      setTest(await testConnection());
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="settings">
      <h2>Settings &amp; Integrations</h2>
      <p>
        Connect Atlas to your ServiceNow instance. Your password is stored in the macOS
        Keychain, never in a file. Tip: install the Atlas scoped app on your instance first.
      </p>

      <label>
        <input type="checkbox" checked={s.use_fake}
               onChange={(e) => set({ use_fake: e.target.checked })} />
        Try with demo data (no instance needed)
      </label>

      <fieldset disabled={s.use_fake}>
        <label>Instance URL
          <input value={s.sn_instance_url}
                 onChange={(e) => set({ sn_instance_url: e.target.value })}
                 placeholder="https://yourinstance.service-now.com" />
        </label>
        <label>Username
          <input value={s.sn_oauth_username}
                 onChange={(e) => set({ sn_oauth_username: e.target.value })} />
        </label>
        <label>Password
          <input type="password" value={password}
                 onChange={(e) => setPassword(e.target.value)}
                 placeholder={s.password_set ? "•••••••• (leave blank to keep)" : ""} />
        </label>
        <label>Scope
          <input value={s.sn_scope}
                 onChange={(e) => set({ sn_scope: e.target.value })} />
        </label>
      </fieldset>

      <div className="settings-actions">
        <button disabled={busy} onClick={save}>Save</button>
        <button disabled={busy || s.use_fake} onClick={runTest}>Test connection</button>
      </div>

      {msg && <p className="settings-msg">{msg}</p>}
      {test && (
        <p className={test.ok ? "ok" : "err"}>
          {test.ok ? "✓ Connection OK" : `✗ ${test.error ?? "Failed"}`}
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Wire into `frontend/src/App.tsx`.** Read the current file first, then: add a "Settings" tab/route, and on first load call `getStatus()` — if `!configured && !fake`, show `SettingsView` initially. Keep it consistent with the existing view-switching pattern in `App.tsx` (do not invent a router if the app uses simple state-based view switching). Minimal shape:
```tsx
// pseudocode to adapt to the existing App.tsx pattern:
// const [view, setView] = useState<"now" | "clients" | "settings">("now");
// useEffect(() => { getStatus().then(s => { if (!s.configured && !s.fake) setView("settings"); }); }, []);
// add a nav button: <button onClick={() => setView("settings")}>Settings</button>
// render: {view === "settings" && <SettingsView onSaved={() => setView("now")} />}
```
Implement it concretely against the real `App.tsx` structure (read it first).

- [ ] **Step 5: Build to verify types/compile:**
```bash
cd "$REPO/frontend" && npm run build
```
Expected: tsc + vite succeed.

- [ ] **Step 6: Commit**
```bash
cd "$REPO" && git add frontend/src/types.ts frontend/src/api.ts frontend/src/SettingsView.tsx frontend/src/App.tsx
git commit -m "feat: in-app Settings/Integrations page + first-run + demo toggle"
```

---

## Task 8: Build, smoke-test, document

- [ ] **Step 1: Full backend + desktop suites green**
```bash
cd "$REPO/backend" && ./.venv/bin/python -m pytest -q
cd "$REPO" && ./backend/.venv/bin/python -m pytest desktop/tests -q
```

- [ ] **Step 2: Build and launch the app, exercise Settings**
```bash
cd "$REPO" && bash scripts/build-desktop.sh && open dist/Atlas.app
```
Manually: the window opens; navigate to Settings; toggle "demo data" off; enter a dummy instance/user/password; Save (persists); re-open the app and confirm the values are still there (config.json in `~/Library/Application Support/Atlas/`, password in Keychain). With demo on, the app shows the normal views. (A real Test-connection success requires a reachable instance — expected to fail against a dummy URL, which is correct behavior surfacing the error.)

- [ ] **Step 3: Confirm per-user files**
```bash
cat "$HOME/Library/Application Support/Atlas/config.json"
security find-generic-password -s atlas-sn -a sn_password -w >/dev/null 2>&1 && echo "password in Keychain ✅" || echo "(no password set yet)"
```

- [ ] **Step 4: PROGRESS.md** — add decision **D14**:
```markdown
**D14 — In-app configuration (Plan B), basic auth per D11.** A Settings/Integrations
page configures the ServiceNow connection from inside the app; non-secret settings
persist to `~/Library/Application Support/Atlas/config.json`, the password to the
macOS Keychain (`atlas-sn`). `get_settings()` overlays this on env/.env; `get_sn()`
is dynamic (`reset_sn()` after save) and builds a **basic-auth** live client
(`HttpServiceNow` with httpx `auth=(user,pass)`), matching D11 (OAuth is walled on
`nnash`). New routes: `/api/settings`, `/api/status`, `/api/test-connection`.
Plan: `docs/superpowers/plans/2026-06-03-atlas-in-app-config.md`.
```

- [ ] **Step 5: Commit**
```bash
cd "$REPO" && git add docs/PROGRESS.md
git commit -m "docs: record in-app configuration (D14)"
```

---

## Done criteria
- All backend tests green (existing 36 + new: paths 3, user_config 3, config_overlay 2, servicenow_auth 2, main_deps 3, settings_api 6).
- Desktop tests green (server 3 + paths 3).
- `Atlas.app` opens, Settings page saves/loads per-user config, password lands in Keychain (not config.json), demo toggle works, Test-connection surfaces success/failure.

## Self-review checklist (run after writing the plan)
- Spec coverage: Settings page ✅, per-user config ✅, Keychain secret ✅, status/first-run ✅, demo toggle ✅, test-connection ✅. OAuth `/oauth/callback` intentionally replaced by basic auth (D11) — flagged at top.
- No placeholders except the App.tsx wiring, which is explicitly "adapt to the real file" with concrete pseudocode (the implementer must read App.tsx — it's small).
- Type consistency: `AppSettings`/`AppStatus`/`TestResult` used identically across types.ts, api.ts, SettingsView.tsx; `_NON_SECRET` keys match the pydantic field names and the SettingsIn model; `reset_sn`/`get_sn`/`get_settings`/`load_overlay`/`save_config`/`save_password`/`get_password` consistent across tasks.
