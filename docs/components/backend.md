# Component: Backend (FastAPI service)

**Purpose:** Orchestrate everything the cockpit needs — read/write ServiceNow, (later) pull
Microsoft Graph, (later) call Anthropic and generate decks — and expose a small JSON API to
the local React frontend. Runs as `localhost:8000` on the work Mac.

**Location:** `backend/`

## Boundaries (what this component may and may not do)
- ✅ Talk to ServiceNow **only** through the `ServiceNowClient` interface (`app/servicenow.py`).
  Never scatter raw `httpx` calls to SN around the routers.
- ✅ Default to `FakeServiceNow` (`USE_FAKE=true`). The live `HttpServiceNow` is selected only
  by config on the work Mac.
- ❌ Never hold secrets in code. All config comes from `Settings` (`app/config.py`) → `.env` /
  Keychain. See [CLAUDE.md](../../CLAUDE.md) rule #2.
- ❌ No corporate data persisted to disk on the personal Mac during dev. Tests use the in-memory fake only.

## Guardrails
- **All SN access is mockable.** If you add a feature, it must work against `FakeServiceNow` in
  a test before it ever touches the live instance.
- **Routers stay thin.** Endpoints validate input (pydantic models in `app/models.py`) and call
  the SN client. Ordering/business rules (e.g. Now-view sort) live in clearly named helpers,
  not inline magic.
- **Deterministic core.** The Now ordering is `priority rank → due_date → commitment`. Do not
  make it depend on an AI call (see CLAUDE.md rule #6).
- **`get_sn` is the single DI seam** (`app/main_deps.py`), overridden in tests. Keep it that way —
  don't construct SN clients ad hoc inside routers.
- **TDD.** Every endpoint/behavior gets a failing test first.

## Key files
| File | Responsibility |
|------|----------------|
| `app/config.py` | env-driven `Settings` (USE_FAKE, SN URL/scope/OAuth) |
| `app/models.py` | pydantic `Client`, `Task` (mirror SN fields + TS types) |
| `app/servicenow.py` | `ServiceNowClient` protocol, `FakeServiceNow`, `HttpServiceNow` |
| `app/auth.py` | `TokenManager` — OAuth password→refresh, Keychain cache |
| `app/main.py` | FastAPI app, CORS, health, router includes |
| `app/main_deps.py` | `get_sn` dependency (fake-vs-http selection) |
| `app/routers/clients.py` · `tasks.py` | the JSON API |

## How to extend (Plan 2+)
1. Add the pydantic model (mirror the SN table fields in [DATA-MODEL](../DATA-MODEL.md)).
2. Add a router using `get_sn`; table name = `f"{settings.sn_scope}_<table>"`.
3. Write tests against `FakeServiceNow` first.
4. Keep new cross-record logic (timelines, prep assembly) in named service functions, tested in isolation.

## Run / test
```bash
cd backend && source .venv/bin/activate
pytest -v                              # all tests, against the fake
USE_FAKE=true uvicorn app.main:app --reload --port 8000   # serve locally
```
