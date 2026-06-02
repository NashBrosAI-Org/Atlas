# Atlas — Progress Tracker

Update this **after each unit of work**, not at session end. (Per the user's standing
preference for living progress docs.)

Last updated: 2026-06-02

## Current status
- **Phase:** P1 (SN-backed cockpit foundation) — in progress.
- **Active plan:** [`superpowers/plans/2026-06-02-atlas-foundation.md`](superpowers/plans/2026-06-02-atlas-foundation.md) (Plan 1).
- **Branch:** `feature/atlas-foundation`.

## Plan 1 task status
| Task | What | Status | Where it runs |
|------|------|--------|---------------|
| 1–6 | ServiceNow scoped app + full schema | ⏳ TODO — **user does in instance** | ServiceNow (work) |
| 7 | FastAPI scaffold | ✅ done | personal Mac |
| 8 | Config + Client/Task models | ✅ done | personal Mac |
| 9 | ServiceNowClient interface + FakeServiceNow | ✅ done | personal Mac |
| 10 | HttpServiceNow + OAuth TokenManager | ✅ done | personal Mac |
| 11 | FastAPI wiring + DI + health | ✅ done | personal Mac |
| 12 | Clients API | ✅ done | personal Mac |
| 13 | Tasks API + deterministic Now ordering | ✅ done | personal Mac |
| 14 | React Now view (frontend) | ✅ done | personal Mac |
| 15 | Point at live instance + export Update Set | ⏳ TODO — **user, work Mac**, after recon | work Mac |

**Backend test status:** 13/13 passing (`cd backend && source .venv/bin/activate && pytest -v`).
Note: running on Python 3.14.5 (newer than the 3.11+ target); a benign httpx/starlette
deprecation warning appears but no failures.

**Frontend status:** Vite React-TS builds clean (`npm run build`, zero TS errors); Now view
renders the priority-ordered task list with client filter; verified `/api/now` ordering and
dev server serving 200 against the mock. **Plan 1 code tasks (7–14) are complete** — what
remains is the ServiceNow-side build (Tasks 1–6) and go-live (Task 15), both user-side.

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

## Next plans (not started)
- **Plan 2 — Records & capture:** Contacts (+org chart), Notes/RAID UI, Engagements, Themes, Meetings, Transcripts (manual upload), Client dossier view.
- **Plan 3 — Awareness:** Activity timeline, stale-client radar, Links, Tags, KeyDates + reminders, scheduled export/backup job.
- **Plan P2 — M365:** Entra recon → email + calendar, email→task, auto-association, meeting-prep assembler, morning briefing.
- **Plan P3 — AI & decks:** Anthropic summaries/drafting/prioritization, RAG search, `.pptx` + web decks on official ServiceNow brand kit.
