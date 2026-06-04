# Atlas

A client-centric command center for juggling multiple customer accounts. A **native macOS desktop
app** (`Atlas.app`) — FastAPI + React running as one local process in a native window — backed by a
ServiceNow scoped app; Microsoft 365 (email/calendar) and AI (summaries, decks, search) layer on in
later phases.

## Read these first
- **[CLAUDE.md](CLAUDE.md)** — project guardrails + conventions. Read before changing anything.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — the three tiers and where data is allowed to live.
- [docs/DATA-MODEL.md](docs/DATA-MODEL.md) — the Client-centric schema.
- [docs/PROGRESS.md](docs/PROGRESS.md) — current status, what's done, what's next.

## Components (each has its own guardrail charter)
- [docs/components/backend.md](docs/components/backend.md) — FastAPI orchestrator
- [docs/components/servicenow.md](docs/components/servicenow.md) — scoped-app backend / system of record
- [docs/components/frontend.md](docs/components/frontend.md) — React UI

## Implementation plans
- Plan 1 — [foundation slice](docs/superpowers/plans/2026-06-02-atlas-foundation.md)
- Plan 2 — [client dossier](docs/superpowers/plans/2026-06-02-atlas-dossier.md)
- Desktop app — [design spec](docs/superpowers/specs/2026-06-02-atlas-desktop-app-design.md) · [A: shell](docs/superpowers/plans/2026-06-03-atlas-desktop-shell.md) · [B: in-app config](docs/superpowers/plans/2026-06-03-atlas-in-app-config.md) · [C: distribution](docs/superpowers/plans/2026-06-03-atlas-shareable-distribution.md)

## Run as a desktop app
```bash
bash scripts/install.sh    # builds Atlas.app, installs to ~/Applications, opens it
```
Needs Node and Python 3.10–3.13. Built locally, so macOS trusts it (no Apple Developer ID needed).
Configure your ServiceNow connection inside the app (Settings tab); demo mode needs no instance.
Sharing it with someone else: [docs/SHARING.md](docs/SHARING.md).

## Quickstart (development, against the mock — no live instance needed)
```bash
# backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q                                    # all green
USE_FAKE=true uvicorn app.main:app --reload --port 8000

# frontend (separate terminal)
cd frontend && npm install && npm run dev    # http://localhost:5173
```

## The one rule that matters most
**No corporate data on the personal Mac.** Develop against the in-memory fake; the live
ServiceNow instance and real credentials are touched only on the work Mac. See CLAUDE.md.
