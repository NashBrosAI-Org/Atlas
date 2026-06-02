# Cockpit Foundation Implementation Plan (Plan 1 of the P1 series)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working, testable vertical slice of the client cockpit — a ServiceNow scoped app holding the full data model, plus a local FastAPI + React app that reads/writes **Clients** and **Tasks** and renders a prioritized "Now" view — developed entirely against a mock ServiceNow so no live instance or corporate data is touched.

**Architecture:** ServiceNow scoped app is the backend/database (designed to migrate to CSM/PPM later). A local Python FastAPI service runs on the work Mac, talks to ServiceNow over the Table REST API using OAuth 2.0, and exposes a small JSON API to a local React/Vite frontend. The ServiceNow integration sits behind a `ServiceNowClient` interface with an in-memory `FakeServiceNow` implementation, so the whole backend is built and tested with TDD here on the personal Mac. The live instance is only contacted on the work Mac via config.

**Tech Stack:** ServiceNow (scoped app, Table API, OAuth 2.0) · Python 3.11+ / FastAPI / httpx / pydantic / pytest · React + Vite + TypeScript · macOS Keychain for the OAuth refresh token.

---

## Scope boundary (read this first)

**This plan delivers:** the full SN schema (all tables defined once), OAuth wiring, and a Client+Task tracer bullet (CRUD + Now view) proven against a mock.

**This plan does NOT deliver (future plans in the P1 series):**
- Plan 2: Contacts (+ org chart), Notes/RAID, Meetings, Transcripts (manual upload), Engagements, Themes — backend + UI.
- Plan 3: Client dossier view, Activity timeline, Links, Tags, KeyDates, export/backup job.
- Plan P2-*: Microsoft Graph (email + calendar) — gated on the Entra recon spike.
- Plan P3-*: AI (summaries/drafting/prioritization), decks (.pptx + web), semantic search.

**Hard rules carried from design (do not violate):**
1. No corporate M365 data ever lands on the personal Mac. Plan 1 has zero M365 surface, so this is automatic — development uses only mock/synthetic data.
2. Secrets (OAuth client secret, refresh token) never enter the repo. They live in `.env` (gitignored) and/or the macOS Keychain.
3. SN table/field names mirror CSM/PPM concepts so a later migration is a mapping, not a rebuild.

---

## P0 — Recon spike for Plan 1 (do these on the WORK Mac before/while building)

These are **user actions, not code**. They only gate the "point at the live instance" step (Task 14); the entire build through Task 13 runs against the mock and needs none of them.

- [ ] **R1 — Proxy reach:** From the work Mac, confirm `curl -sS -o /dev/null -w "%{http_code}\n" https://<your-instance>.service-now.com/api/now/table/sys_user?sysparm_limit=1 -u <user>:<pass>` returns a `200`/`401` (reached), not a proxy block/timeout. If blocked, Plan 1's live step is deferred until the proxy allows `*.service-now.com`.
- [ ] **R2 — OAuth app registration in SN:** Confirm you can reach **All > System OAuth > Application Registry** in your instance (you have full access, so this should be yes). Task 12 creates the registration.
- [ ] **R3 — App Engine Studio / Studio availability:** Confirm you can open **All > App Engine Studio** (or classic **Studio**) to build a scoped app. If App Engine Studio is unavailable, classic Studio works too (Task 1 notes both paths).

(M365/Entra and Teams-transcript recon belong to the P2 plan, not here.)

---

## File / artifact structure

**ServiceNow (built in the instance, captured in an Update Set):**
- Scoped app `Client Cockpit` (scope auto-prefixed, e.g. `x_<vendor>_cockpit`).
- Tables (full model, created once): `client`, `contact`, `engagement`, `theme`, `task`, `meeting`, `transcript`, `email`, `note`, `deck`, `key_date`, `link`, `tag`, `tag_m2m`.
- One OAuth API endpoint registration for the local app.

**Local repo `client-cockpit/`:**
```
backend/
  app/
    __init__.py
    config.py            # env-driven settings (instance URL, OAuth, USE_FAKE flag)
    models.py            # pydantic models: Client, Task (Plan 1 subset)
    servicenow.py        # ServiceNowClient protocol + HttpServiceNow + FakeServiceNow
    auth.py              # OAuth token acquisition + refresh, Keychain storage
    main.py              # FastAPI app, dependency wiring
    routers/
      __init__.py
      clients.py         # /api/clients endpoints
      tasks.py           # /api/tasks endpoints (incl. Now ordering)
  tests/
    conftest.py          # fixtures: app + FakeServiceNow
    test_servicenow_fake.py
    test_clients_api.py
    test_tasks_api.py
    test_now_ordering.py
  pyproject.toml         # or requirements.txt
  .env.example
frontend/
  (Vite React-TS scaffold)
  src/
    api.ts               # typed fetch wrappers
    types.ts             # Client, Task TS types (mirror pydantic)
    NowView.tsx          # the prioritized task list + client filter
    App.tsx
docs/superpowers/plans/2026-06-02-cockpit-foundation.md   # this file
```

---

## ServiceNow data model reference (authoritative field list)

Plan 1 **creates all tables** (Tasks 1–11) but the **app only wires Client + Task** (Tasks 5–13). Field types use ServiceNow column types.

> Table label → name. Scope prefix is auto-generated; below uses logical names. "ref→X" = Reference to table X. "choice" = Choice list.

**client** (→ future CSM Account)
- `name` (String, 120, display) · `short_code` (String, 12) · `status` (choice: active/prospect/dormant, default active) · `email_domains` (String, 500 — comma-separated for now) · `notes` (String, 4000)

**contact** (→ future CSM Contact)
- `name` (String, 120, display) · `email` (String, 120) · `phone` (String, 40) · `client` (ref→client) · `role_title` (String, 120) · `reports_to` (ref→contact) · `personal_notes` (String, 4000) · `sentiment` (choice: champion/neutral/detractor, default neutral)

**engagement** (→ future PPM Project)
- `name` (String, 120, display) · `client` (ref→client) · `status` (choice: on_track/at_risk/blocked/done, default on_track) · `start_date` (Date) · `target_date` (Date) · `description` (String, 4000)

**theme**
- `name` (String, 120, display) · `client` (ref→client) · `status` (choice: open/watching/resolved, default open) · `description` (String, 4000)

**task**
- `title` (String, 200, display) · `client` (ref→client) · `engagement` (ref→engagement) · `theme` (ref→theme) · `priority` (choice: critical/high/medium/low, default medium) · `due_date` (Date) · `promised_date` (Date) · `is_commitment` (True/False, default false) · `status` (choice: open/in_progress/waiting/done, default open) · `source` (choice: manual/email/meeting, default manual)

**meeting**
- `title` (String, 200, display) · `client` (ref→client) · `engagement` (ref→engagement) · `datetime` (Date/Time) · `type` (choice: teams/zoom/other, default teams) · `attendees` (String, 1000) · `summary` (String, 8000)

**transcript**
- `meeting` (ref→meeting) · `client` (ref→client) · `full_text` (String, 1,000,000 — "Max length" large) · `source` (choice: teams/zoom/manual, default manual) · `captured_date` (Date/Time)

**email**
- `subject` (String, 300, display) · `client` (ref→client) · `from_addr` (String, 200) · `to_addr` (String, 1000) · `received_date` (Date/Time) · `body` (String, 1,000,000) · `graph_message_id` (String, 200, unique index)

**note**
- `title` (String, 200, display) · `body` (String, 8000) · `note_type` (choice: general/risk/issue/decision, default general — this is RAID) · `target` (Document ID field — polymorphic pin to any table/record) · `pinned` (True/False, default false)

**deck**
- `title` (String, 200, display) · `client` (ref→client) · `engagement` (ref→engagement) · `output_type` (choice: pptx/site) · `location_url` (String, 1000) · `status` (choice: draft/final, default draft)

**key_date**
- `title` (String, 200, display) · `type` (choice: renewal/qbr/contract_end/birthday/milestone) · `date` (Date) · `recurring` (True/False, default false) · `reminder_lead_days` (Integer, default 7) · `client` (ref→client) · `contact` (ref→contact)

**link**
- `title` (String, 200, display) · `url` (String, 1000) · `client` (ref→client)

**tag**
- `name` (String, 60, display, unique index)

**tag_m2m** (many-to-many join)
- `tag` (ref→tag) · `target` (Document ID field — polymorphic)

---

# TASKS

## Task 1: Create the ServiceNow scoped app

**Artifact:** New scoped application in your instance, plus a dedicated Update Set so all Plan 1 config is portable to other instances.

- [ ] **Step 1: Start an Update Set**

In the instance: **All > System Update Sets > Local Update Sets > New**. Name: `Client Cockpit - Plan 1`. Save, then click **Make this my current set**.

- [ ] **Step 2: Create the scoped app**

Open **All > App Engine Studio** → **Create app** → **Build from scratch**. Name: `Client Cockpit`. Description: `Personal client-management cockpit`. Leave roles default. (Classic path: **All > Studio > Create Application** → scratch.) Note the generated scope name (e.g. `x_<vendor>_cockpit`) — record it in `backend/.env.example` as a comment.

- [ ] **Step 3: Verify**

Confirm the app appears under **All > App Engine Studio > (your apps)** and that the scope shows in the app's settings. No automated test — this is platform config captured by the Update Set.

---

## Task 2: Create the `client` table

**Artifact:** Table `client` in the cockpit scope with the fields from the reference above.

- [ ] **Step 1: Create the table**

In App Engine Studio → **Data > Add > Table**. Label `Client`, name auto-fills. Add columns exactly per the **client** reference (name, short_code, status [choice], email_domains, notes). Set `name` as the **Display** value (table → Controls → "Display" on the `name` column, or mark it display when creating).

- [ ] **Step 2: Verify**

Open **All > (scope) > Clients > New**, create a record `name=Acme Corp, short_code=ACME, status=active`. Save. Confirm it lists. Leave the record — Task 13 uses it.

---

## Task 3: Create the `contact` table

- [ ] **Step 1:** Create table `Contact` with fields per the **contact** reference. `reports_to` is a Reference column pointing back to `contact` (self-reference). `name` is Display.
- [ ] **Step 2:** Create one record `name=Jane Doe, email=jane@acme.com, client=Acme Corp, role_title=VP IT, sentiment=champion`. Verify it saves and the `client` reference resolves.

---

## Task 4: Create the `engagement` and `theme` tables

- [ ] **Step 1:** Create table `Engagement` per reference (status choice on_track/at_risk/blocked/done). `name` Display.
- [ ] **Step 2:** Create table `Theme` per reference (status choice open/watching/resolved). `name` Display.
- [ ] **Step 3:** Verify each by creating one record tied to `client=Acme Corp`.

---

## Task 5: Create the `task` table

**Artifact:** Table `task` — the spine of the Now view.

- [ ] **Step 1:** Create table `Task` with **all** fields per the **task** reference: title (Display), client (ref), engagement (ref), theme (ref), priority (choice critical/high/medium/low default medium), due_date (Date), promised_date (Date), is_commitment (True/False default false), status (choice open/in_progress/waiting/done default open), source (choice manual/email/meeting default manual).
- [ ] **Step 2:** Create two records:
  - `title=Send Acme SOW, client=Acme Corp, priority=high, status=open, is_commitment=true, due_date=<tomorrow>`
  - `title=Review Acme tickets, client=Acme Corp, priority=medium, status=open, due_date=<in 5 days>`
- [ ] **Step 3:** Verify both list under the Task table.

---

## Task 6: Create the remaining tables (meeting, transcript, email, note, deck, key_date, link, tag, tag_m2m)

These complete the model for future plans. Create them now while you're in the schema; the app won't call them until Plan 2+.

- [ ] **Step 1:** Create `meeting`, `transcript`, `email`, `deck`, `key_date`, `link` per their references.
- [ ] **Step 2:** Create `note` — for `target` use a **Document ID** column type (this is SN's polymorphic pointer). For `note_type` use the choice general/risk/issue/decision.
- [ ] **Step 3:** Create `tag` (name unique) and `tag_m2m` (tag ref + Document ID `target`).
- [ ] **Step 4:** Verify each table exists under the scope. No records needed.

---

## Task 7: Scaffold the FastAPI backend project

**Files:**
- Create: `backend/pyproject.toml`, `backend/app/__init__.py`, `backend/.env.example`

- [ ] **Step 1: Create the venv and install deps**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "fastapi>=0.115" "uvicorn[standard]>=0.30" "httpx>=0.27" "pydantic>=2.7" "pydantic-settings>=2.3" "pytest>=8" "pytest-asyncio>=0.23" "keyring>=25"
pip freeze > requirements.txt
```

- [ ] **Step 2: Create `backend/.env.example`**

```bash
# Copy to .env (gitignored) on the WORK Mac and fill in. Leave USE_FAKE=true on the personal Mac.
USE_FAKE=true
SN_INSTANCE_URL=https://YOUR-INSTANCE.service-now.com
SN_SCOPE=x_vendor_cockpit            # the scope from Task 1 Step 2
SN_OAUTH_CLIENT_ID=
SN_OAUTH_CLIENT_SECRET=              # do NOT commit; use Keychain in prod (see auth.py)
SN_OAUTH_USERNAME=
SN_OAUTH_PASSWORD=
```

- [ ] **Step 3: Create `backend/app/__init__.py`** (empty file).

- [ ] **Step 4: Commit**

```bash
cd ..
git add backend/pyproject.toml backend/requirements.txt backend/app/__init__.py backend/.env.example .gitignore
git commit -m "chore: scaffold FastAPI backend"
```

---

## Task 8: Define config and pydantic models

**Files:**
- Create: `backend/app/config.py`, `backend/app/models.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_models.py`:
```python
from app.models import Task, Client

def test_task_defaults():
    t = Task(title="Send SOW", client="abc123")
    assert t.priority == "medium"
    assert t.status == "open"
    assert t.is_commitment is False
    assert t.source == "manual"

def test_client_minimal():
    c = Client(name="Acme Corp")
    assert c.status == "active"
    assert c.sys_id is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.models'`

- [ ] **Step 3: Create `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    use_fake: bool = True
    sn_instance_url: str = "https://example.service-now.com"
    sn_scope: str = "x_vendor_cockpit"
    sn_oauth_client_id: str = ""
    sn_oauth_client_secret: str = ""
    sn_oauth_username: str = ""
    sn_oauth_password: str = ""


def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Create `backend/app/models.py`**

```python
from typing import Literal, Optional
from pydantic import BaseModel

Priority = Literal["critical", "high", "medium", "low"]
TaskStatus = Literal["open", "in_progress", "waiting", "done"]
TaskSource = Literal["manual", "email", "meeting"]
ClientStatus = Literal["active", "prospect", "dormant"]


class Client(BaseModel):
    sys_id: Optional[str] = None
    name: str
    short_code: Optional[str] = None
    status: ClientStatus = "active"
    email_domains: Optional[str] = None
    notes: Optional[str] = None


class Task(BaseModel):
    sys_id: Optional[str] = None
    title: str
    client: Optional[str] = None          # sys_id of a Client
    engagement: Optional[str] = None
    theme: Optional[str] = None
    priority: Priority = "medium"
    due_date: Optional[str] = None        # ISO date string
    promised_date: Optional[str] = None
    is_commitment: bool = False
    status: TaskStatus = "open"
    source: TaskSource = "manual"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
cd .. && git add backend/app/config.py backend/app/models.py backend/tests/test_models.py && git commit -m "feat: config + Client/Task models"
```

---

## Task 9: ServiceNow client interface + in-memory fake

**Files:**
- Create: `backend/app/servicenow.py`
- Test: `backend/tests/test_servicenow_fake.py`

The interface mirrors the SN Table API (list/get/create/update) generically over a table name and a dict payload. `FakeServiceNow` implements it in memory so all higher layers are testable without a network.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_servicenow_fake.py`:
```python
import pytest
from app.servicenow import FakeServiceNow


@pytest.mark.asyncio
async def test_create_and_get():
    sn = FakeServiceNow()
    created = await sn.create("task", {"title": "A", "priority": "high"})
    assert created["sys_id"]
    got = await sn.get("task", created["sys_id"])
    assert got["title"] == "A"


@pytest.mark.asyncio
async def test_list_filters_by_query():
    sn = FakeServiceNow()
    await sn.create("task", {"title": "A", "client": "c1"})
    await sn.create("task", {"title": "B", "client": "c2"})
    rows = await sn.list("task", query={"client": "c1"})
    assert [r["title"] for r in rows] == ["A"]


@pytest.mark.asyncio
async def test_update_merges_fields():
    sn = FakeServiceNow()
    c = await sn.create("task", {"title": "A", "status": "open"})
    updated = await sn.update("task", c["sys_id"], {"status": "done"})
    assert updated["status"] == "done"
    assert updated["title"] == "A"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_servicenow_fake.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.servicenow'`

- [ ] **Step 3: Create `backend/app/servicenow.py`**

```python
from typing import Protocol, Optional
import itertools


class ServiceNowClient(Protocol):
    async def list(self, table: str, query: Optional[dict] = None) -> list[dict]: ...
    async def get(self, table: str, sys_id: str) -> Optional[dict]: ...
    async def create(self, table: str, payload: dict) -> dict: ...
    async def update(self, table: str, sys_id: str, payload: dict) -> dict: ...


class FakeServiceNow:
    """In-memory stand-in for the SN Table API. Used in tests and on the
    personal Mac (USE_FAKE=true) so no live instance is required."""

    def __init__(self) -> None:
        self._tables: dict[str, dict[str, dict]] = {}
        self._ids = itertools.count(1)

    def _table(self, table: str) -> dict[str, dict]:
        return self._tables.setdefault(table, {})

    async def list(self, table: str, query: Optional[dict] = None) -> list[dict]:
        rows = list(self._table(table).values())
        if query:
            rows = [r for r in rows if all(r.get(k) == v for k, v in query.items())]
        return rows

    async def get(self, table: str, sys_id: str) -> Optional[dict]:
        return self._table(table).get(sys_id)

    async def create(self, table: str, payload: dict) -> dict:
        sys_id = f"fake{next(self._ids):06d}"
        record = {**payload, "sys_id": sys_id}
        self._table(table)[sys_id] = record
        return record

    async def update(self, table: str, sys_id: str, payload: dict) -> dict:
        record = self._table(table)[sys_id]
        record.update(payload)
        return record
```

- [ ] **Step 4: Configure pytest-asyncio**

Append to `backend/pyproject.toml` (create the file with this content if it doesn't exist):
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_servicenow_fake.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
cd .. && git add backend/app/servicenow.py backend/tests/test_servicenow_fake.py backend/pyproject.toml && git commit -m "feat: ServiceNow client interface + in-memory fake"
```

---

## Task 10: HTTP ServiceNow client (real Table API)

**Files:**
- Modify: `backend/app/servicenow.py` (add `HttpServiceNow`)
- Create: `backend/app/auth.py`
- Test: `backend/tests/test_http_servicenow.py`

`HttpServiceNow` implements the same interface against `/api/now/table/{table}`. The query dict is encoded as a `sysparm_query` string (`field=value^field2=value2`). Auth comes from `auth.py` (OAuth password grant for v1 simplicity; refresh token cached in Keychain).

- [ ] **Step 1: Write the failing test** (uses httpx MockTransport — no network)

`backend/tests/test_http_servicenow.py`:
```python
import httpx
import pytest
from app.servicenow import HttpServiceNow


def _client(handler) -> HttpServiceNow:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport, base_url="https://x.service-now.com")
    return HttpServiceNow(http, token_provider=lambda: "tok")


@pytest.mark.asyncio
async def test_list_builds_sysparm_query():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"result": [{"sys_id": "1", "title": "A"}]})

    sn = _client(handler)
    rows = await sn.list("task", query={"client": "c1", "status": "open"})
    assert rows == [{"sys_id": "1", "title": "A"}]
    assert "sysparm_query=client%3Dc1%5Estatus%3Dopen" in seen["url"]
    assert seen["auth"] == "Bearer tok"


@pytest.mark.asyncio
async def test_create_posts_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(201, json={"result": {"sys_id": "9", "title": "New"}})

    sn = _client(handler)
    created = await sn.create("task", {"title": "New"})
    assert created["sys_id"] == "9"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_http_servicenow.py -v`
Expected: FAIL with `ImportError: cannot import name 'HttpServiceNow'`

- [ ] **Step 3: Add `HttpServiceNow` to `backend/app/servicenow.py`**

```python
# add at top of file:
from typing import Callable
import httpx


# add at end of file:
class HttpServiceNow:
    """Real SN Table API client. Same interface as FakeServiceNow."""

    def __init__(self, http: httpx.AsyncClient, token_provider: Callable[[], str]) -> None:
        self._http = http
        self._token = token_provider

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token()}", "Accept": "application/json"}

    @staticmethod
    def _encode_query(query: dict) -> str:
        return "^".join(f"{k}={v}" for k, v in query.items())

    async def list(self, table, query=None):
        params = {"sysparm_display_value": "false", "sysparm_exclude_reference_link": "true"}
        if query:
            params["sysparm_query"] = self._encode_query(query)
        r = await self._http.get(f"/api/now/table/{table}", params=params, headers=self._headers())
        r.raise_for_status()
        return r.json()["result"]

    async def get(self, table, sys_id):
        r = await self._http.get(f"/api/now/table/{table}/{sys_id}", headers=self._headers())
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()["result"]

    async def create(self, table, payload):
        r = await self._http.post(f"/api/now/table/{table}", json=payload, headers=self._headers())
        r.raise_for_status()
        return r.json()["result"]

    async def update(self, table, sys_id, payload):
        r = await self._http.patch(f"/api/now/table/{table}/{sys_id}", json=payload, headers=self._headers())
        r.raise_for_status()
        return r.json()["result"]
```

- [ ] **Step 4: Create `backend/app/auth.py`** (OAuth password grant + Keychain cache)

```python
import time
import httpx
import keyring
from app.config import Settings

_KEYRING_SERVICE = "client-cockpit-sn"


class TokenManager:
    """Acquires and refreshes a ServiceNow OAuth token. Caches the refresh
    token in the macOS Keychain so the client secret/password aren't needed
    after first login."""

    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    def _token_url(self) -> str:
        return f"{self._s.sn_instance_url}/oauth_token.do"

    def get_token(self) -> str:
        if self._access_token and time.time() < self._expires_at - 30:
            return self._access_token
        refresh = keyring.get_password(_KEYRING_SERVICE, "refresh_token")
        data = {
            "client_id": self._s.sn_oauth_client_id,
            "client_secret": self._s.sn_oauth_client_secret,
        }
        if refresh:
            data |= {"grant_type": "refresh_token", "refresh_token": refresh}
        else:
            data |= {
                "grant_type": "password",
                "username": self._s.sn_oauth_username,
                "password": self._s.sn_oauth_password,
            }
        resp = httpx.post(self._token_url(), data=data, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        self._access_token = body["access_token"]
        self._expires_at = time.time() + int(body.get("expires_in", 1800))
        if body.get("refresh_token"):
            keyring.set_password(_KEYRING_SERVICE, "refresh_token", body["refresh_token"])
        return self._access_token
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_http_servicenow.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
cd .. && git add backend/app/servicenow.py backend/app/auth.py backend/tests/test_http_servicenow.py && git commit -m "feat: HTTP ServiceNow client + OAuth token manager"
```

---

## Task 11: FastAPI app wiring + dependency injection

**Files:**
- Create: `backend/app/main.py`, `backend/tests/conftest.py`
- Test: `backend/tests/test_health.py`

`main.py` chooses `FakeServiceNow` when `USE_FAKE=true`, else builds `HttpServiceNow` with a real httpx client + `TokenManager`. A `get_sn` dependency is overridable in tests.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_health.py`:
```python
from fastapi.testclient import TestClient
from app.main import app

def test_health():
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_health.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Create `backend/app/main.py`**

```python
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.servicenow import FakeServiceNow, HttpServiceNow, ServiceNowClient
from app.auth import TokenManager

app = FastAPI(title="Client Cockpit")
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
```

- [ ] **Step 4: Create router package + placeholders so imports resolve**

`backend/app/routers/__init__.py` (empty). Create `backend/app/routers/clients.py` and `backend/app/routers/tasks.py` each with:
```python
from fastapi import APIRouter
router = APIRouter()
```

- [ ] **Step 5: Create `backend/tests/conftest.py`** (fresh fake per test)

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app, get_sn
from app.servicenow import FakeServiceNow


@pytest.fixture
def sn() -> FakeServiceNow:
    return FakeServiceNow()


@pytest.fixture
def client(sn):
    app.dependency_overrides[get_sn] = lambda: sn
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 6: Run to verify it passes**

Run: `pytest tests/test_health.py -v`
Expected: PASS (1 passed)

- [ ] **Step 7: Commit**

```bash
cd .. && git add backend/app/main.py backend/app/routers backend/tests/conftest.py backend/tests/test_health.py && git commit -m "feat: FastAPI app wiring + DI + health endpoint"
```

---

## Task 12: Clients API

**Files:**
- Modify: `backend/app/routers/clients.py`
- Test: `backend/tests/test_clients_api.py`

Table name is `{scope}_client`; the router uses `f"{settings.sn_scope}_client"`. For the fake, the table name is just a string key, so tests pass regardless of scope.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_clients_api.py`:
```python
def test_create_and_list_clients(client):
    r = client.post("/api/clients", json={"name": "Acme Corp", "short_code": "ACME"})
    assert r.status_code == 201
    created = r.json()
    assert created["sys_id"]
    assert created["status"] == "active"

    r2 = client.get("/api/clients")
    assert r2.status_code == 200
    names = [c["name"] for c in r2.json()]
    assert "Acme Corp" in names
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_clients_api.py -v`
Expected: FAIL — 404/405 (endpoints not implemented)

- [ ] **Step 3: Implement `backend/app/routers/clients.py`**

```python
from fastapi import APIRouter, Depends
from app.config import get_settings
from app.models import Client
from app.servicenow import ServiceNowClient
from app.main_deps import get_sn  # see note in Step 4

router = APIRouter(prefix="/api/clients", tags=["clients"])
_settings = get_settings()


def _table() -> str:
    return f"{_settings.sn_scope}_client"


@router.get("")
async def list_clients(sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    return await sn.list(_table())


@router.post("", status_code=201)
async def create_client(body: Client, sn: ServiceNowClient = Depends(get_sn)) -> dict:
    payload = body.model_dump(exclude_none=True, exclude={"sys_id"})
    return await sn.create(_table(), payload)
```

- [ ] **Step 4: Break the circular import — move `get_sn` to `app/main_deps.py`**

Create `backend/app/main_deps.py`:
```python
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
```
Then in `backend/app/main.py` replace the inline `get_sn` definition and the `_fake`/`get_settings` usage with `from app.main_deps import get_sn` (keep the `app.include_router` lines). Update `backend/tests/conftest.py` import to `from app.main import app` and `from app.main_deps import get_sn`.

- [ ] **Step 5: Run to verify it passes**

Run: `pytest tests/test_clients_api.py tests/test_health.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
cd .. && git add backend/app && git commit -m "feat: Clients API (list/create)"
```

---

## Task 13: Tasks API + Now ordering

**Files:**
- Modify: `backend/app/routers/tasks.py`
- Test: `backend/tests/test_tasks_api.py`, `backend/tests/test_now_ordering.py`

The Now ordering is deterministic (no AI): sort by priority rank (critical=0…low=3), then by `due_date` ascending (None last), then commitments before non-commitments at equal rank/date. Done tasks are excluded from Now.

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_tasks_api.py`:
```python
def test_create_and_list_tasks(client):
    r = client.post("/api/tasks", json={"title": "Send SOW", "priority": "high", "is_commitment": True})
    assert r.status_code == 201
    assert r.json()["sys_id"]
    rows = client.get("/api/tasks").json()
    assert any(t["title"] == "Send SOW" for t in rows)

def test_update_task_status(client):
    sid = client.post("/api/tasks", json={"title": "X"}).json()["sys_id"]
    r = client.patch(f"/api/tasks/{sid}", json={"status": "done"})
    assert r.status_code == 200
    assert r.json()["status"] == "done"
```

`backend/tests/test_now_ordering.py`:
```python
def test_now_orders_by_priority_then_due(client):
    client.post("/api/tasks", json={"title": "low-soon", "priority": "low", "due_date": "2026-06-03"})
    client.post("/api/tasks", json={"title": "crit-later", "priority": "critical", "due_date": "2026-06-30"})
    client.post("/api/tasks", json={"title": "high-nodate", "priority": "high"})
    client.post("/api/tasks", json={"title": "done-task", "priority": "critical", "status": "done"})

    rows = client.get("/api/now").json()
    titles = [t["title"] for t in rows]
    assert "done-task" not in titles                      # done excluded
    assert titles[0] == "crit-later"                       # critical first
    assert titles.index("high-nodate") < titles.index("low-soon")

def test_now_filters_by_client(client):
    client.post("/api/tasks", json={"title": "for-a", "client": "A"})
    client.post("/api/tasks", json={"title": "for-b", "client": "B"})
    rows = client.get("/api/now?client=A").json()
    assert [t["title"] for t in rows] == ["for-a"]
```

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test_tasks_api.py tests/test_now_ordering.py -v`
Expected: FAIL — endpoints not implemented.

- [ ] **Step 3: Implement `backend/app/routers/tasks.py`**

```python
from typing import Optional
from fastapi import APIRouter, Depends
from app.config import get_settings
from app.models import Task
from app.servicenow import ServiceNowClient
from app.main_deps import get_sn

router = APIRouter(prefix="/api", tags=["tasks"])
_settings = get_settings()

_PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _table() -> str:
    return f"{_settings.sn_scope}_task"


def _now_sort_key(t: dict):
    rank = _PRIORITY_RANK.get(t.get("priority", "medium"), 2)
    due = t.get("due_date") or "9999-12-31"
    commit = 0 if str(t.get("is_commitment")) in ("True", "true", "1") else 1
    return (rank, due, commit)


@router.get("/tasks")
async def list_tasks(sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    return await sn.list(_table())


@router.post("/tasks", status_code=201)
async def create_task(body: Task, sn: ServiceNowClient = Depends(get_sn)) -> dict:
    payload = body.model_dump(exclude_none=True, exclude={"sys_id"})
    return await sn.create(_table(), payload)


@router.patch("/tasks/{sys_id}")
async def update_task(sys_id: str, body: dict, sn: ServiceNowClient = Depends(get_sn)) -> dict:
    return await sn.update(_table(), sys_id, body)


@router.get("/now")
async def now_view(client: Optional[str] = None, sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    query = {"client": client} if client else None
    rows = await sn.list(_table(), query=query)
    rows = [t for t in rows if t.get("status") != "done"]
    return sorted(rows, key=_now_sort_key)
```

- [ ] **Step 4: Run to verify they pass**

Run: `pytest -v`
Expected: PASS (all tests across the suite green)

- [ ] **Step 5: Commit**

```bash
cd .. && git add backend/app/routers/tasks.py backend/tests/test_tasks_api.py backend/tests/test_now_ordering.py && git commit -m "feat: Tasks API + deterministic Now ordering"
```

---

## Task 14: React frontend — Now view

**Files:**
- Create (via Vite scaffold): `frontend/` then `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/NowView.tsx`, `frontend/src/App.tsx`

Manual verification (no automated FE tests in Plan 1 — UI is thin and proven by clicking).

- [ ] **Step 1: Scaffold Vite + React + TS**

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
```

- [ ] **Step 2: Create `frontend/src/types.ts`**

```ts
export interface Client { sys_id?: string; name: string; short_code?: string; status?: string; }
export interface Task {
  sys_id?: string; title: string; client?: string;
  priority?: "critical" | "high" | "medium" | "low";
  due_date?: string; is_commitment?: boolean; status?: string;
}
```

- [ ] **Step 3: Create `frontend/src/api.ts`**

```ts
import type { Client, Task } from "./types";
const BASE = "http://localhost:8000/api";

export async function getClients(): Promise<Client[]> {
  return (await fetch(`${BASE}/clients`)).json();
}
export async function getNow(client?: string): Promise<Task[]> {
  const q = client ? `?client=${encodeURIComponent(client)}` : "";
  return (await fetch(`${BASE}/now${q}`)).json();
}
export async function createTask(t: Partial<Task>): Promise<Task> {
  return (await fetch(`${BASE}/tasks`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(t),
  })).json();
}
export async function completeTask(sys_id: string): Promise<Task> {
  return (await fetch(`${BASE}/tasks/${sys_id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "done" }),
  })).json();
}
```

- [ ] **Step 4: Create `frontend/src/NowView.tsx`**

```tsx
import { useEffect, useState } from "react";
import type { Client, Task } from "./types";
import { getClients, getNow, completeTask } from "./api";

export function NowView() {
  const [clients, setClients] = useState<Client[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<string>("");

  const refresh = () => getNow(filter || undefined).then(setTasks);
  useEffect(() => { getClients().then(setClients); }, []);
  useEffect(() => { refresh(); }, [filter]);

  return (
    <div style={{ maxWidth: 720, margin: "2rem auto", fontFamily: "system-ui" }}>
      <h1>Now</h1>
      <select value={filter} onChange={(e) => setFilter(e.target.value)}>
        <option value="">All clients</option>
        {clients.map((c) => <option key={c.sys_id} value={c.sys_id}>{c.name}</option>)}
      </select>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {tasks.map((t) => (
          <li key={t.sys_id} style={{ display: "flex", gap: 8, padding: "8px 0", borderBottom: "1px solid #eee" }}>
            <span style={{ width: 70, fontWeight: 600 }}>{t.priority}</span>
            <span style={{ flex: 1 }}>{t.is_commitment ? "🤝 " : ""}{t.title}</span>
            <span style={{ width: 100, color: "#888" }}>{t.due_date ?? "—"}</span>
            <button onClick={() => completeTask(t.sys_id!).then(refresh)}>Done</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 5: Replace `frontend/src/App.tsx`**

```tsx
import { NowView } from "./NowView";
export default function App() { return <NowView />; }
```

- [ ] **Step 6: Manual verification — run the whole stack against the fake**

Terminal 1 (backend, fake mode):
```bash
cd backend && source .venv/bin/activate && USE_FAKE=true uvicorn app.main:app --reload --port 8000
```
Seed a client + tasks:
```bash
curl -s -X POST localhost:8000/api/clients -H 'content-type: application/json' -d '{"name":"Acme Corp","short_code":"ACME"}'
curl -s -X POST localhost:8000/api/tasks -H 'content-type: application/json' -d '{"title":"Send Acme SOW","priority":"high","is_commitment":true,"due_date":"2026-06-03"}'
curl -s -X POST localhost:8000/api/tasks -H 'content-type: application/json' -d '{"title":"Review Acme tickets","priority":"medium","due_date":"2026-06-08"}'
```
Terminal 2 (frontend):
```bash
cd frontend && npm run dev
```
Open `http://localhost:5173`. Expected: "Now" lists "Send Acme SOW" (high, 🤝) above "Review Acme tickets" (medium). Clicking **Done** removes the task from the list. The client dropdown shows "Acme Corp".

- [ ] **Step 7: Commit**

```bash
cd .. && git add frontend && git commit -m "feat: React Now view (frontend tracer bullet)"
```

---

## Task 15: Point at the live ServiceNow instance (WORK Mac only)

Do this only after P0 recon R1–R3 pass, on the work Mac, against your real (clean) instance.

- [ ] **Step 1: Register the OAuth app in SN**

In the instance: **All > System OAuth > Application Registry > New > Create an OAuth API endpoint for external clients**. Name `Client Cockpit Local`. Note the generated **Client ID** and **Client Secret**. Set **Refresh Token Lifespan** to a comfortable value (e.g. 8,640,000 s = 100 days).

- [ ] **Step 2: Fill `.env` on the work Mac** (never commit)

Copy `backend/.env.example` → `backend/.env`, set `USE_FAKE=false`, `SN_INSTANCE_URL`, `SN_SCOPE` (the Task 1 scope), `SN_OAUTH_CLIENT_ID/SECRET`, and your `SN_OAUTH_USERNAME/PASSWORD` for the first token exchange.

- [ ] **Step 3: Smoke-test the live token + list**

```bash
cd backend && source .venv/bin/activate
python -c "from app.config import get_settings; from app.auth import TokenManager; print(TokenManager(get_settings()).get_token()[:12], '...')"
```
Expected: prints the first chars of an access token (and caches the refresh token in Keychain). If it errors, re-check the OAuth registration and credentials.

- [ ] **Step 4: Run the stack live and verify**

Start uvicorn **without** `USE_FAKE` (so `.env` `USE_FAKE=false` applies), open the frontend, and confirm the Client + Tasks you created in Tasks 2/5 (Acme Corp, the two tasks) appear in the Now view — proving the real Table API path end-to-end.

- [ ] **Step 5: Export the Update Set (archive durability begins)**

In the instance: **System Update Sets > (your set) > Mark Complete > Export to XML**. Save the XML into the repo under `servicenow/updateset/` (config only — no data) and commit. This is the first piece of the "instance is not infinite → keep your own copy" rule.

```bash
git add servicenow/updateset/*.xml && git commit -m "chore: export SN scoped-app update set"
```

---

## Self-Review (completed by author)

**Spec coverage (Plan-1 scope):** SN scoped app ✓ (Tasks 1–6), full schema incl. CSM/PPM-aligned names + polymorphic Note + commitment/promised_date + RAID note_type ✓ (reference + Task 5/6), OAuth 2.0 + Keychain ✓ (Task 10/15), local FastAPI+React on the Mac ✓ (Tasks 7–14), mock-first dev / no corporate data on personal Mac ✓ (FakeServiceNow, USE_FAKE), deterministic Now (no AI) ✓ (Task 13), client filter ✓ (Task 13/14), update-set export as first archive step ✓ (Task 15). Out-of-scope items (Contacts UI, Meetings, Transcripts, M365, AI, decks, dossier, timeline, export job) explicitly deferred to named future plans.

**Placeholder scan:** No TBD/"handle edge cases"/"similar to" — every code step shows full code. The one inter-task refactor (circular import) is spelled out in Task 12 Step 4 with the exact new file.

**Type consistency:** `ServiceNowClient` methods `list/get/create/update` identical across `FakeServiceNow`, `HttpServiceNow`, and Protocol. `get_sn` lives in `app/main_deps.py` and is the single override point used by both routers and `conftest.py`. Model field names (`is_commitment`, `due_date`, `promised_date`, `short_code`) match between pydantic (`models.py`), the SN reference, and the TS types.

---

## Future plans (do not build here)
- **Plan 2 — Records & capture:** Contacts (+org chart), Notes/RAID UI, Engagements, Themes, Meetings, Transcripts (manual upload + full-text storage), Client dossier view.
- **Plan 3 — Awareness:** Activity timeline, stale-client radar, Links, Tags, KeyDates + reminders, scheduled export/backup job.
- **Plan P2 — M365:** Entra recon spike → email + calendar read, email→task, auto-association, meeting-prep assembler, morning briefing.
- **Plan P3 — AI & decks:** Anthropic API summaries/drafting/prioritization, semantic search (RAG), `.pptx` + web decks on the official ServiceNow brand kit.
