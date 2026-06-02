# CLAUDE.md — Atlas

Project guardrails and conventions for anyone (human or agent) working in this repo. Read the
**Hard rules** before changing anything; they override convenience.

## What Atlas is
A client-centric command center for juggling ~6 customer accounts. **ServiceNow scoped app** =
backend/system-of-record. **Local FastAPI (`:8000`) + React/Vite (`:5173`)** on the work Mac =
the daily UI (not a ServiceNow Workspace). Microsoft 365 (email/calendar) and AI (summaries,
decks, search) layer on in later phases. Full picture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Hard rules (the guardrails)

1. **No corporate M365 data on the personal Mac.** Develop against `FakeServiceNow` / synthetic
   data only. Real credentials and the live instance are touched **only on the work Mac**.
   *Why:* corporate email/calendar content must not land on uncontrolled hardware.
2. **Secrets never enter the repo.** OAuth secret, refresh token, passwords live in `backend/.env`
   (gitignored) and the macOS Keychain (`keyring` service `atlas-sn`). Only `.env.example` is committed.
3. **The SN employee instance is NOT a durable archive** (it can be reclaimed). Export/backup of
   transcripts + emails + the Update Set is **mandatory** — the instance is never the only copy.
4. **Retention-past-policy is an accepted, named risk.** Routing email/meeting content into SN to
   retain it beyond the company's retention window is a legal/compliance risk the user has
   consciously accepted and owns with IT. Keep it visible; don't silently broaden retained data.
5. **Schema names mirror CSM/PPM** (Client→Account, Engagement→Project, Contact→Contact) so a
   later migration is a mapping, not a rebuild.
6. **AI is additive, not core.** The "Now" view is deterministic (priority → due_date → commitment).
   No feature may *require* the Anthropic API to function.
7. **Dev → clone, never copy data.** Code flows through git to the work Mac; data never does.

### Named risks (keep current)
| # | Risk | Mitigation |
|---|------|-----------|
| R1 | Retention past company policy (legal/compliance) | User owns w/ IT; rule #4 |
| R2 | Employee instance "not infinite" → data loss | Mandatory export/backup (rule #3) |
| R3 | Entra app-reg / Graph + Teams-transcript perms may need IT | Recon spike gates P2 |
| R4 | Work-laptop proxy may block `*.service-now.com` / Graph | Recon before go-live |

## Conventions

**Workflow & git** (per the user's global WORKFLOW.md)
- Branch per change: `feature/…`, `fix/…`, `chore/…`. Never commit straight to `main`.
- Commit messages: one line, present-tense imperative ("add Now ordering").
- Tests pass and no debug code before merging.

**Python (backend)**
- FastAPI + pydantic v2; endpoints are `async`. Python 3.11+ target.
- **All ServiceNow access goes through the `ServiceNowClient` interface** (`app/servicenow.py`);
  `get_sn` (`app/main_deps.py`) is the single DI seam, overridden in tests. No ad-hoc SN clients.
- Routers stay thin: validate (pydantic models in `app/models.py`) → call the client. Cross-record
  logic (ordering, prep assembly) lives in named helpers, not inline magic.
- **TDD:** failing test first, against `FakeServiceNow`. `pytest` (`asyncio_mode=auto`).

**TypeScript / React (frontend)**
- `src/types.ts` mirrors the backend pydantic models — change both together.
- The frontend calls **only** `http://localhost:8000/api`. No direct SN/Graph calls, no secrets in
  the browser. Small, focused view files.

**General**
- One responsibility per file; keep files small enough to hold in context.
- **Update [docs/PROGRESS.md](docs/PROGRESS.md) after each unit of work**, not at session end.
  Record significant decisions in its **Decisions** log.

## Docs index
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — tiers, data flow, phasing
- [docs/DATA-MODEL.md](docs/DATA-MODEL.md) — Client-centric schema
- [docs/PROGRESS.md](docs/PROGRESS.md) — status tracker + **decision log (ADR-style)**
- [docs/components/](docs/components/) — per-component charters (each with its own guardrails)
- [docs/superpowers/plans/](docs/superpowers/plans/) — implementation plans

## Run / test
```bash
# backend (against the mock — no live instance needed)
cd backend && source .venv/bin/activate && pytest -v
USE_FAKE=true uvicorn app.main:app --reload --port 8000
# frontend (separate terminal; needs backend on :8000)
cd frontend && npm run dev
```
