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
| 14 | React Now view (frontend) | 🔜 next | personal Mac |
| 15 | Point at live instance + export Update Set | ⏳ TODO — **user, work Mac**, after recon | work Mac |

**Backend test status:** 13/13 passing (`cd backend && source .venv/bin/activate && pytest -v`).
Note: running on Python 3.14.5 (newer than the 3.11+ target); a benign httpx/starlette
deprecation warning appears but no failures.

## User to-do (cannot be automated from here)
- [ ] P0 recon on the **work Mac**: R1 proxy reach to `*.service-now.com`, R2 OAuth Application Registry access, R3 App Engine Studio access.
- [ ] Plan 1 Tasks 1–6: build the scoped app + 14 tables in the instance (capture in an Update Set).
- [ ] Plan 1 Task 15: register OAuth endpoint, fill `.env` on work Mac, go live, export Update Set.

## Next plans (not started)
- **Plan 2 — Records & capture:** Contacts (+org chart), Notes/RAID UI, Engagements, Themes, Meetings, Transcripts (manual upload), Client dossier view.
- **Plan 3 — Awareness:** Activity timeline, stale-client radar, Links, Tags, KeyDates + reminders, scheduled export/backup job.
- **Plan P2 — M365:** Entra recon → email + calendar, email→task, auto-association, meeting-prep assembler, morning briefing.
- **Plan P3 — AI & decks:** Anthropic summaries/drafting/prioritization, RAG search, `.pptx` + web decks on official ServiceNow brand kit.
