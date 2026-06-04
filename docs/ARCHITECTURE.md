# Atlas — Architecture

Atlas is a **client-centric command center** for someone juggling ~6 customer accounts. It is
a local app on the work Mac, backed by a ServiceNow scoped app, with Microsoft 365 and AI
layered on later.

## The three tiers (sorted by what's allowed to live where)

| Tier | Holds | Why allowed |
|------|-------|-------------|
| **ServiceNow employee instance** (cloud) | Tasks, clients, contacts, meetings, transcripts, emails, notes, synthetic/demo data — the system of record | User-controlled corporate-adjacent cloud; also the skill-building + demo surface |
| **Work Mac — local** | `Atlas.app` (the packaged FastAPI + React app), per-user config (`~/Library/Application Support/Atlas/config.json`) + Keychain credentials, generated `.pptx`, *transient* M365 pulls, export/backup files | Sanctioned corporate hardware |
| **Personal Mac — dev only** | Source code, mocks, synthetic fixtures | Never corporate data (see [CLAUDE.md](../CLAUDE.md) rule #1) |

## Shape

```
              Atlas.app — native macOS window (pywebview + PyInstaller)
                         │  packaged = ONE local process
ServiceNow scoped app   ▼
   (DB + workflows)   FastAPI service (127.0.0.1, work Mac)  ──►  Microsoft Graph  (email/cal — P2)
        ▲   Table REST   │   serves the built React UI at /    ──►  Anthropic API    (AI — P3, additive)
        │   API, basic   │   JSON API under /api               ──►  python-pptx + web (decks — P3)
        └───auth (D11)───┤
                         ▼
                  React UI  (served same-origin when packaged; Vite dev server :5173 in dev)
```

## Key design decisions
- **SN is the backend, the local app is the frontend.** No ServiceNow Workspace UI — the
  custom React app is the daily surface.
- **Delivered as a native macOS desktop app.** FastAPI serves the built React bundle from one
  local process inside a pywebview window; PyInstaller bundles it into `Atlas.app`, installed via
  `scripts/install.sh` (built locally → no Gatekeeper quarantine, **no Apple Developer ID**).
  Configured in-app via a Settings page: non-secrets in `~/Library/Application Support/Atlas/config.json`,
  the ServiceNow password in the macOS Keychain. The live ServiceNow connection uses **basic auth**
  (OAuth is walled on `nnash` — decision D11). See plans A/B/C in [superpowers/plans/](superpowers/plans/).
- **ServiceNow access sits behind an interface** (`ServiceNowClient`) with an in-memory
  `FakeServiceNow`, so the whole backend is built and tested with **no live instance and no
  corporate data** on the personal Mac.
- **Awareness is computed, not stored** (Plan 3a). `app/awareness.py` aggregates an activity
  timeline + stale-client radar from existing records on read (`/api/awareness/*`); nothing new is
  persisted. Records are time-ordered by domain date or `sys_created_on` — `FakeServiceNow` now
  stamps `sys_created_on`/`sys_updated_on`, and awareness **normalizes timestamps** to handle both
  the fake's ISO-`Z` form and live ServiceNow's `YYYY-MM-DD HH:MM:SS` (relevant when wiring live data).
- **Deterministic-first.** The core value (what to work on) is plain task management, not AI.
- **Migration-friendly schema** (CSM/PPM-aligned names) — see [DATA-MODEL](DATA-MODEL.md).

## Phasing
- **P1** — SN-backed command center (manual entry, manual transcript upload). *Plan 1 = foundation slice.*
- **P2** — Microsoft 365 (email + calendar), gated on the Entra recon spike.
- **P3** — AI (summaries/drafting/prioritization), semantic search, decks (`.pptx` + web, SN brand).
