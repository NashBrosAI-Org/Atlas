# Atlas Awareness Views (Plan 3a) — Design Spec

**Date:** 2026-06-03
**Status:** Approved (brainstorming) → ready for implementation plan
**Scope:** The first slice of Plan 3 (Awareness): an **activity timeline** and a **stale-client radar**, surfaced both globally (a new Awareness tab) and per-client (in the dossier).

## Problem
Atlas tracks tasks, meetings, transcripts, notes, and engagements per client, but there's no way to see **what's been happening** or **which accounts have gone quiet**. Juggling ~6 accounts, the easiest one to drop is the one you haven't touched in weeks. Plan 3a adds awareness: a chronological activity view and a radar that flags cooling/stale clients.

## Decisions (locked during brainstorming)
1. **Both surfaces.** A global **Awareness** tab (recent-activity feed + stale radar) *and* a per-client **Timeline** in the dossier. They share one aggregation core.
2. **Backend computes, frontend renders.** All aggregation lives in `app/awareness.py` + thin endpoints; the React views just display (per CLAUDE.md: thin frontend, logic in named helpers, testable against `FakeServiceNow`).
3. **Configurable, tiered radar.** Two thresholds — `cooling_days` (default 14) and `stale_days` (default 30) — editable in Settings, persisted in `config.json` (Plan B overlay). Active clients only.
4. **Record timestamps.** Add `sys_created_on` (+ `sys_updated_on`) to `FakeServiceNow`; live ServiceNow already returns them, so timeline/radar behave identically in demo and live.

## Scope boundaries
- **In scope:** the awareness core, three read endpoints, the two thresholds in Settings, the Awareness tab, the dossier Timeline section, tests.
- **Out of scope (other Plan 3 slices):** tags (3b), key dates + reminders (3c), scheduled export/backup (3d), "Links". Also out: task *completion* events on the timeline (v1 shows creation events + current status; completion-events can come later), and any AI summarization of activity.

**Assumed working dir:** worktree root `/Users/nick/Atlas/.claude/worktrees/desktop-app` (`$REPO`). Backend venv `$REPO/backend/.venv` (run from `backend/`). Tables are `f"{sn_scope}_<entity>"`; demo scope defaults to `x_vendor_atlas`.

---

## Architecture

```
FakeServiceNow / HttpServiceNow      (records now carry sys_created_on / sys_updated_on)
            │
       app/awareness.py              ← pure aggregation, unit-tested
   build_timeline / recent_activity / stale_radar
            │
   routers/awareness.py              ← thin endpoints
   /api/awareness/activity · /timeline/{client_id} · /radar
            │
   React: AwarenessView (tab)  +  DossierView "Timeline" section
```

## Components

### 1. Record timestamps (`backend/app/servicenow.py`)
`FakeServiceNow.create` stamps `sys_created_on` and `sys_updated_on` (ISO-8601 UTC, e.g. `2026-06-03T14:00:00Z`); `update` refreshes `sys_updated_on`. `HttpServiceNow` is unchanged — live ServiceNow already returns these fields. This gives every record a sortable time. *Risk:* returned dicts gain two fields; the plan must re-run the full suite and fix any test asserting exact dict shape (most assert specific keys, so low risk).

To keep the fake testable with controlled times (not wall-clock), `FakeServiceNow.__init__` accepts an optional `clock: Callable[[], datetime]` (defaults to `datetime.now(timezone.utc)`); tests inject a fake clock to place records at known instants.

### 2. `app/awareness.py` (the shared core)
An **event** is `{ "type": str, "title": str, "when": str(iso), "client": str(sys_id), "client_name": str, "status": Optional[str] }`.

- `event_time(record, domain_field) -> str` — returns the domain date (`meeting.datetime`, `transcript.captured_date`) if present, else `sys_created_on`. Single source of "when".
- `async build_timeline(sn, scope, client_id) -> list[event]` — gather the client's meetings/transcripts/tasks/notes/engagements, map each to an event, sort newest-first.
- `async recent_activity(sn, scope, limit=50) -> list[event]` — every client's events, tagged with `client_name`, newest-first, capped at `limit`.
- `async stale_radar(sn, scope, cooling_days, stale_days) -> list[radar_entry]` — for each **active** client, `last_activity = max(when of its events)` or the client's own `sys_created_on` if it has none; classify `stale` (quiet ≥ stale_days), else `cooling` (≥ cooling_days), else omit; sort most-overdue first. `radar_entry = { client, client_name, last_activity, days_quiet, tier }`.

Day math uses an injectable `now` (default `datetime.now(timezone.utc)`) so tier boundaries are unit-testable.

### 3. Endpoints (`backend/app/routers/awareness.py`, thin)
- `GET /api/awareness/activity?limit=50` → `recent_activity`
- `GET /api/awareness/timeline/{client_id}` → `build_timeline` (404 if client absent)
- `GET /api/awareness/radar` → `stale_radar` using `get_settings().cooling_days/stale_days`

All resolve `scope` from `get_settings().sn_scope` and the client via `get_sn()` (the existing DI seam).

### 4. Config (`backend/app/config.py`, `routers/settings.py`, frontend)
Add `cooling_days: int = 14` and `stale_days: int = 30` to `Settings`. Add them to the settings router's `_NON_SECRET` allowlist + `SettingsIn`, and to the React Settings page (two number inputs under a "Radar thresholds" group). They flow through the existing `config.json` overlay — no new storage.

### 5. Frontend
- `frontend/src/types.ts`: `ActivityEvent`, `RadarEntry`; extend `AppSettings` with `cooling_days`, `stale_days`.
- `frontend/src/api.ts`: `getActivity()`, `getTimeline(clientId)`, `getRadar()`.
- `frontend/src/AwarenessView.tsx`: a "Needs attention" radar panel (cooling = amber, stale = red; each row → opens the dossier) above a "Recent activity" feed (grouped/iconed by type). New `"awareness"` entry in the `App.tsx` `View` union + nav button.
- `frontend/src/DossierView.tsx`: a "Timeline" section calling `getTimeline(client_sys_id)`.

## Data flow
1. User opens **Awareness** → `getRadar()` + `getActivity()` → backend aggregates current records → panels render.
2. User opens a **dossier** → existing dossier load + `getTimeline(id)` → timeline section renders.
3. User edits thresholds in **Settings** → `PUT /api/settings` (Plan B) → `config.json` → next `/radar` call reflects them.

## Error handling
- Empty store (e.g. configured-but-empty live instance) → empty feed/radar, not an error.
- Client not found on timeline → 404 (consistent with the dossier route).
- Frontend uses the existing `http<T>` helper (throws on non-2xx; surfaced in the view).

## Testing
- `awareness.py` unit tests against `FakeServiceNow` with an injected clock: timeline ordering; domain-date-beats-created precedence; `recent_activity` cross-client + limit; radar tier boundaries (just-under/just-over each threshold); active-only filter; no-activity client classified by its own age.
- Endpoint tests via `TestClient` (incl. timeline 404).
- Settings round-trip test extended for the two new fields.
- Frontend verified via `npm run build`.
- Full backend suite must stay green after the timestamp change.

## Self-review
- Spec coverage: timeline ✅, radar ✅, both surfaces ✅, configurable tiered thresholds ✅, timestamp foundation ✅, tests ✅.
- No placeholders. Consistent types (`event` shape, `radar_entry`) used across core/endpoints/frontend.
- Scope: one cohesive slice (shared core powers all three reads); other Plan-3 features explicitly deferred.
- Ambiguity resolved: "activity" = creation/domain-date of child records; "stale" = active clients quiet ≥ thresholds; timeline v1 = creation events (no completion events).
