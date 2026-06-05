# backend/ — guardrails (auto-loaded here)

Full rules: repo root [CLAUDE.md](../CLAUDE.md) (hard rules + risks) ·
[docs/CODE-STANDARDS.md](../docs/CODE-STANDARDS.md) · [docs/components/backend.md](../docs/components/backend.md).

Quick reminders when editing here:
- **External access only via interfaces:** `ServiceNowClient` (`app/servicenow.py`, DI seam `get_sn`),
  `GraphClient` (`app/graph.py`, `get_graph`), `AIClient` (`app/ai.py`, `get_ai`). Each has a `Fake*`
  for tests/demo and a live impl wired only when configured. No ad-hoc clients.
- **Routers stay thin:** validate via pydantic models (`app/models.py`) → call the client. Cross-record
  logic goes in pure-logic modules (`awareness`, `m365`, `briefing`, `summaries`, `ordering`).
- **AI is additive (rule #6):** only `/api/ai/*`, gated by `ai_enabled` (server-side) with a `FakeAI`
  fallback. Nothing else may call the AI.
- **TDD first**, against the fakes, `pytest` (`asyncio_mode=auto`); inject a clock/`today` for
  time-based logic. Tables: `f"{sn_scope}_<entity>"`.
- Run: `source .venv/bin/activate && pytest -v` · `USE_FAKE=true uvicorn app.main:app --reload`.
