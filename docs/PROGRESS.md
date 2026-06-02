# Atlas — Progress Tracker

Update this **after each unit of work**, not at session end. (Per the user's standing
preference for living progress docs.)

Last updated: 2026-06-02

## Current status
- **Phase:** P1 (SN-backed command center foundation) — **Plans 1 & 2 code complete**.
- **Plans done:** [`superpowers/plans/2026-06-02-atlas-foundation.md`](superpowers/plans/2026-06-02-atlas-foundation.md) (Plan 1), [`superpowers/plans/2026-06-02-atlas-dossier.md`](superpowers/plans/2026-06-02-atlas-dossier.md) (Plan 2).
- **Branch:** `main` (canonical). No feature branches open. No git remote yet — Atlas deploys by `git clone`/`pull` to the work Mac, not to a server.
- **Next:** Plan 3 (Awareness) or the P2 M365 recon spike. The only blockers to *using* Atlas are user-side (ServiceNow build + go-live).

## Plan 1 task status — COMPLETE (code)
| Task | What | Status | Where it runs |
|------|------|--------|---------------|
| 1–6 | ServiceNow scoped app + full 14-table schema | ⏳ TODO — **user does in instance** | ServiceNow (work) |
| 7–13 | FastAPI backend (config, models, ServiceNowClient + FakeServiceNow, HttpServiceNow + OAuth, DI, Clients/Tasks API, deterministic Now ordering) | ✅ done | personal Mac |
| 14 | React Now view | ✅ done | personal Mac |
| 15 | Point at live instance + export Update Set | ⏳ TODO — **user, work Mac**, after recon | work Mac |

Plan-1 final review fixes applied: live-mode SN client is now a process-wide singleton (connection pool + token cache reused), `types.ts` synced to the backend `Task` model, commitment-tiebreaker + HttpServiceNow get/update tests added.

## Plan 2 task status — COMPLETE (code)
| Task | What | Status |
|------|------|--------|
| 1 | Pydantic models: Contact/Engagement/Theme/Meeting/Transcript/Note | ✅ done |
| 2 | Generic `crud_router(name, suffix, Model)` factory (DRY — one factory, six entities) | ✅ done |
| 3 | Wire the six entity routers | ✅ done |
| 4 | Polymorphic Note pinning round-trip (`target_table` + `target_id`) | ✅ done |
| 5 | `GET /api/clients/{id}/dossier` aggregate (client + contacts/engagements/themes/open tasks/meetings/notes) | ✅ done |
| 6 | Frontend types + api calls | ✅ done |
| 7 | OrgChart component (`reports_to` tree, sentiment badges) | ✅ done |
| 8 | NoteComposer + TranscriptPaste (paste-text → SN) | ✅ done |
| 9 | ClientsView + DossierView + minimal routing | ✅ done |
| 10 | End-to-end verification | ✅ done — dossier confirmed against a running mock server |

**Backend test status:** **30/30 passing** (`cd backend && source .venv/bin/activate && pytest -q`). Plan 1 = 17 (incl. review-fix tests), Plan 2 = 13.
**Frontend status:** builds clean (`npm run build`, zero TS errors, no new deps); Now view + Clients list + Dossier page (org chart, transcript paste, note composer) all wired to `http://localhost:8000/api`.

## User to-do (cannot be automated from here)
- [ ] P0 recon on the **work Mac**: R1 proxy reach to `*.service-now.com`, R2 OAuth Application Registry access, R3 App Engine Studio access.
- [ ] Plan 1 Tasks 1–6: build the scoped app + 14 tables in the instance (capture in an Update Set).
- [ ] Plan 1 Task 15: register OAuth endpoint, fill `.env` on work Mac, go live, export Update Set.

## Decisions (ADR-style log)

Significant decisions and their rationale, newest last. Add an entry when a real fork is resolved.

**D1 — ServiceNow is the backend; a custom local app is the frontend.**
Context: full access to a clean SN employee instance; the user wants to control the UI and not
work inside a ServiceNow Workspace. Decision: SN scoped app = data/system-of-record; React+FastAPI
on the work Mac = the daily surface. Consequence: one custom UI codebase; SN reached via REST/OAuth.

**D2 — Data-residency relaxed: email/meeting content may live in the SN instance.**
Context: originally "all data stays on the laptop," then the user chose to route email content into
SN so it drives the app and survives the company's ~annual retention window. Decision: allow it;
the user owns the legal/compliance risk with IT (risk R1). Consequence: SN holds retained content;
the local SQLite-for-sensitive-data tier is dropped. **Highest-risk decision — stays visible.**

**D3 — Lightweight custom scoped-app tables now; CSM/PPM migration later.**
Context: skill-building + demo goals, but CSM/PPM are heavy. Decision: custom tables with
CSM/PPM-aligned names (Client→Account, Engagement→Project, Contact→Contact). Consequence: clean
daily model + better demo; future migration is a mapping, not a rebuild.

**D4 — Deterministic prioritization in v1; AI is additive.**
Context: the user doesn't need AI auto-prioritization to start. Decision: "Now" view sorts by
priority → due_date → commitment, in plain code. Consequence: no feature depends on the Anthropic
API; AI (summaries/drafting/decks/search) is Phase 3.

**D5 — Develop on the personal Mac against mocks; clone to the work Mac.**
Context: corporate data can't touch the personal Mac. Decision: build behind a `ServiceNowClient`
interface with an in-memory `FakeServiceNow` (`USE_FAKE=true`); real creds/instance only on the work
Mac. Consequence: full TDD here with zero corporate data; the work Mac is the only place go-live happens.

**D6 — Transcripts' full text retained in SN, plus an export/backup.**
Context: the user needs meeting content for years; the instance is "not infinite." Decision: store
full transcript text in SN AND export/back it up so the instance is never the only copy (risk R2).

**D7 — One generic `crud_router` factory, not per-entity routers (Plan 2).**
Context: six near-identical CRUD entities. Decision: a single `crud_router(name, table_suffix, Model)`
factory builds list/create/get/patch for any entity; the dossier is a separate read-only aggregate
helper. Consequence: DRY backend, one test path covers all six; Notes pin polymorphically via
`target_table`+`target_id` with no special-casing.

**D8 — Concurrent `/btw` fork session reconciled onto `main`.**
Context: a parallel session built the frontend + docs while this session built the backend, both in
the same checkout. Decision: isolate each track in its own `git worktree`; `main` is the canonical
integration point (Plan 1 + Plan 2 + the review fixes). Consequence: never share a working tree
across sessions again — worktree-per-session (now also a committed rule in `CLAUDE.md`).

## Next plans (not started)
- **Plan 3 — Awareness:** Activity timeline, stale-client radar, Links, Tags, KeyDates + reminders, scheduled export/backup job.
- **Plan P2 — M365:** Entra recon → email + calendar, email→task, auto-association, meeting-prep assembler, morning briefing.
- **Plan P3 — AI & decks:** Anthropic summaries/drafting/prioritization, RAG search, `.pptx` + web decks on official ServiceNow brand kit.
