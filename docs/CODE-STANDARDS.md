# Atlas — Code Standards

Per-language conventions. The **hard rules**, named risks, and the worktree workflow live in the
always-loaded [CLAUDE.md](../CLAUDE.md); this file is the detail an agent loads when actually writing
code. Each area also has a charter under [components/](components/), and `backend/`, `frontend/`, and
`servicenow/` carry a thin `CLAUDE.md` that points here and auto-loads when you work in that subtree.

## Python (backend)
- FastAPI + pydantic v2; endpoints are `async`. Python 3.11+ target.
- **All ServiceNow access goes through the `ServiceNowClient` interface** (`app/servicenow.py`);
  `get_sn` (`app/main_deps.py`) is the single DI seam, overridden in tests. No ad-hoc SN clients.
- **Microsoft Graph** sits behind `GraphClient` (`app/graph.py`) via `get_graph`; **AI** behind
  `AIClient` (`app/ai.py`) via `get_ai`. Same seam discipline: an in-memory `Fake*` for tests/demo,
  a live `Http*`/`Anthropic*` wired only when configured.
- **AI is additive (rule #6):** only `/api/ai/*` may call the AI; it's gated by `ai_enabled`
  (enforced server-side) and `get_ai()` falls back to `FakeAI`. The deterministic core never depends
  on it.
- Routers stay thin: validate (pydantic models in `app/models.py`) → call the client. Cross-record
  logic (ordering, prep/briefing assembly, summaries) lives in named pure-logic modules
  (`app/awareness.py`, `app/m365.py`, `app/briefing.py`, `app/summaries.py`, `app/ordering.py`), not
  inline in routers.
- Tables are addressed as `f"{sn_scope}_<entity>"`. Cross-entity polymorphic links use
  `target_table` + `target_id` (see Note/tags).
- **TDD:** failing test first, against `FakeServiceNow`/`FakeGraph`/`FakeAI`. `pytest`
  (`asyncio_mode=auto`); inject a clock/`today` for time-dependent logic so tests are deterministic.

## TypeScript / React (frontend)
- `src/types.ts` mirrors the backend pydantic models — change both together.
- The frontend calls **only** the relative `/api` through the `http<T>` helper in `src/api.ts`
  (same-origin when packaged; a Vite dev proxy forwards `/api` → `:8000` in `npm run dev`). No direct
  SN/Graph/AI calls, no secrets in the client.
- Small, focused, single-responsibility view/component files; inline styles consistent with the
  existing components (`SettingsView`, `ClientsView`, the composers). Forms: busy guard +
  `catch → error message`, controlled inputs with `?? ""` fallbacks, stable `key`s.
- Render server strings as text — never `dangerouslySetInnerHTML`; validate user-supplied URL schemes
  to http(s) before using them in an `href` (D21).

## ServiceNow (scoped app)
- Built as **Fluent code via the ServiceNow SDK** (`now-sdk`), *not* hand-built in the UI. The app
  lives in `servicenow/`; deploy with `now-sdk install` to `nnash.service-now.com` (Zurich, MFA on).
  Live backend auth is **basic auth** (OAuth is walled on `nnash` — D11).
- `now-sdk auth` is interactive (OAuth code-paste) — run it in a real/integrated terminal (e.g. VS
  Code), not a background runner. Table/field names follow [DATA-MODEL.md](DATA-MODEL.md),
  CSM/PPM-aligned (rule #5). New backend fields that must persist live also need the Fluent column
  (+ a re-install) — keep model, `types.ts`, and the `.now.ts` table in sync.

## General
- One responsibility per file; keep files small enough to hold in context.
- **Update [PROGRESS.md](PROGRESS.md) after each unit of work**, not at session end; record
  significant decisions in its ADR-style **Decisions** log. Queue smaller ideas in
  [BACKLOG.md](BACKLOG.md).
