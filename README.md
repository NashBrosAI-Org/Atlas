# Atlas

A client-centric work cockpit for juggling multiple customer accounts. Local React + FastAPI
app on the work Mac, backed by a ServiceNow scoped app; Microsoft 365 (email/calendar) and AI
(summaries, decks, search) layer on in later phases.

## Read these first
- **[CLAUDE.md](CLAUDE.md)** — project guardrails + conventions. Read before changing anything.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — the three tiers and where data is allowed to live.
- [docs/DATA-MODEL.md](docs/DATA-MODEL.md) — the Client-centric schema.
- [docs/PROGRESS.md](docs/PROGRESS.md) — current status, what's done, what's next.

## Components (each has its own guardrail charter)
- [docs/components/backend.md](docs/components/backend.md) — FastAPI orchestrator
- [docs/components/servicenow.md](docs/components/servicenow.md) — scoped-app backend / system of record
- [docs/components/frontend.md](docs/components/frontend.md) — React cockpit UI

## Implementation plans
- [docs/superpowers/plans/2026-06-02-atlas-foundation.md](docs/superpowers/plans/2026-06-02-atlas-foundation.md) — Plan 1 (foundation slice)

## Quickstart (development, against the mock — no live instance needed)
```bash
# backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v                                   # 13/13 green
USE_FAKE=true uvicorn app.main:app --reload --port 8000

# frontend (separate terminal)
cd frontend && npm install && npm run dev    # http://localhost:5173
```

## The one rule that matters most
**No corporate data on the personal Mac.** Develop against the in-memory fake; the live
ServiceNow instance and real credentials are touched only on the work Mac. See CLAUDE.md.
