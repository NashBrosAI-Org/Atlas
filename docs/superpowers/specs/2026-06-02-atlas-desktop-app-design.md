# Atlas Desktop App — Design Spec

**Date:** 2026-06-02
**Status:** Approved (brainstorming) → ready for implementation plan
**Scope:** Package Atlas as a shareable native macOS app, configured entirely in-app, with no paid Apple Developer ID.

## Problem

Atlas today is delivered as two local processes (FastAPI `:8000`, Vite `:5173`) opened in a browser tab. There is nowhere good to *host* a web app inside the company, and the only alternative — a ServiceNow portal — is undesirable. We want a clean **desktop app for macOS** that the user (and, later, colleagues) can run without hosting anything.

Key realization: **Atlas is already entirely local** — there is no server to host. The web-app feel is purely a delivery artifact. A desktop app *wraps* the existing stack into one clickable thing; it is a packaging change, not a rewrite. The React UI and FastAPI backend survive intact, and the "frontend calls only `localhost/api`" rule holds.

## Decisions (locked during brainstorming)

1. **Approach A — pywebview + PyInstaller → `Atlas.app`.** A native macOS WKWebView window wrapping the existing app; the whole stack stays in the Python toolchain already in use. (Rejected: Tauri — adds Rust + Python-sidecar packaging; PWA/launcher — least native.)
2. **Shareable, configured in-app.** A **Settings / Integrations page** is the heart of the app: blank slate on first run, the user enters their ServiceNow (and later email) details, hits Connect/Test, and is live. No file editing, no terminal config.
3. **No Apple Developer ID.** ($99/yr rejected.) Consequence: a *downloaded* unsigned app is quarantined and blocked by Gatekeeper. We avoid download-quarantine entirely via **Path 1 — local-build installer**: the recipient runs one command that builds `Atlas.app` *on their own Mac*, so it carries no quarantine flag and macOS trusts it natively. (Rejected: Path 2 — prebuilt + `xattr` unlock; sketchier, per-chip builds.)
4. **Single-process collapse.** FastAPI also serves the **built** React bundle at `/`; API stays under `/api`. One `localhost` process instead of two ports.
5. **Per-user config split** (the bundle is read-only and shared): secrets → macOS Keychain (`keyring`, `atlas-sn`); non-secrets → `~/Library/Application Support/Atlas/config.json`; bundled code/`dist` → read-only inside the `.app`.

## Architecture

```
Atlas.app  (double-click)
   │
   └─ desktop/launcher.py
        ├─ 1. pick a free 127.0.0.1 port
        ├─ 2. start FastAPI (uvicorn) in a background thread
        │       └─ FastAPI serves built React (frontend/dist) at /  +  API at /api
        ├─ 3. wait for /healthz to answer
        └─ 4. open native WKWebView window (pywebview) at http://127.0.0.1:<port>
                └─ closing the window stops the server and exits
```

Nothing about the data flow or guardrails changes — under the hood it is the same FastAPI + React app talking to ServiceNow over `localhost`.

## Components & file layout

New top-level `desktop/` sibling to `backend/`, `frontend/`, `servicenow/`:

| File | Responsibility |
|---|---|
| `desktop/launcher.py` | entrypoint: pick port → start server thread → wait healthy → open webview; teardown on close |
| `desktop/server.py` | build uvicorn `Config`/`Server` for `backend.app.main:app`; thread-friendly start/stop |
| `desktop/paths.py` | resolve bundled (read-only) resources vs per-user data dir; detect `sys.frozen` |
| `desktop/Atlas.spec` | PyInstaller recipe: windowed `.app`, bundle `frontend/dist`, icon, hidden imports |
| `desktop/assets/Atlas.icns` | app icon (placeholder first; real brand later) |
| `scripts/install.sh` | Path-1 installer: preflight → build frontend → build venv → pyinstaller → `~/Applications` |
| `scripts/build-desktop.sh` | dev-side build of `dist/Atlas.app` (used by `install.sh` and CI smoke) |

Minimal touches to existing code (kept behind existing patterns):
- **backend**: mount `StaticFiles` to serve `frontend/dist` at `/` with SPA fallback; add `/healthz`; add thin settings/OAuth/status routes (below). API routes unchanged.
- **frontend**: ensure API base is relative `/api` (works under both vite dev and FastAPI-served packaged app); add the Settings/Integrations page + first-run surface.

## Config, secrets & path resolution

| Kind | Location | Notes |
|---|---|---|
| Bundled, read-only | inside `Atlas.app` (`sys._MEIPASS`) | Python code + built `frontend/dist`; served by FastAPI |
| Per-user, non-secret | `~/Library/Application Support/Atlas/config.json` | SN instance URL, OAuth client_id, M365 tenant/client id, `USE_FAKE`, flags |
| Per-user, secret | macOS Keychain via `keyring` (`atlas-sn`) | SN client_secret + refresh token; per-user automatically |
| Per-user data | `~/Library/Application Support/Atlas/` | logs + mandatory export/backup files (rule #3 / R2) |

`desktop/paths.py` resolves these. The backend's pydantic `Settings` gains a second source: **if frozen → read `config.json` + Keychain; in dev → keep `backend/.env`.** First run with no `config.json` → app boots into the Settings/onboarding surface instead of contacting ServiceNow.

## In-app Settings / Integrations (configured in-app, no files)

The Settings/Integrations page is the primary configuration surface, used for both first-run setup and ongoing management. All in React, served like the rest of the app. Backed by thin, **pre-built** endpoints (written once during development; not generated per-user at runtime):

- `GET/PUT /api/settings` — non-secret config read/write
- `POST /api/connect/servicenow` + `GET /oauth/callback` — OAuth: open SN authorize URL → SN redirects to `http://127.0.0.1:<port>/oauth/callback` → backend swaps code for tokens → tokens to Keychain
- `POST /api/test-connection` — verify SN reachability/creds
- `GET /api/status` — configured? connected? fake-mode?

Runtime behavior: the user types values into the Settings page and saves; the app transparently writes secrets to Keychain and non-secrets to `config.json`; the pre-built endpoints pick them up. The user never edits files or sees the Keychain.

First-run experience: the Settings page front-and-center with a short welcome + **in-app setup instructions**, including the one step the app cannot perform for them — installing the Atlas scoped app on *their* ServiceNow instance (guided steps + a link/help section). A **"Try with demo data"** toggle (`USE_FAKE=true`) lets a user explore before wiring up an instance. An always-available Setup/Help screen lets users re-run steps, reconnect, and see status.

**Caveat (explicit):** the Settings page can test and guide the ServiceNow connection but **cannot remotely create the Atlas scoped app + tables** on a user's instance — that is a separate system requiring deploy to *their* ServiceNow. In-app instructions walk them through it.

## Distribution — `scripts/install.sh` (Path 1)

Recipient gets the repo (git clone or zip) and runs one command:

```
1. Preflight   — check Python 3.11+ and Node; if missing, print exact install hints and stop
2. Build FE    — cd frontend && npm ci && npm run build           → frontend/dist
3. Build venv  — isolated venv; pip install backend + pywebview + pyinstaller
4. Package     — pyinstaller desktop/Atlas.spec                    → dist/Atlas.app
5. Install     — move Atlas.app → ~/Applications, then `open` it
```

Built on their machine → no quarantine flag → launches with no Gatekeeper override. Idempotent: re-running rebuilds/upgrades in place. Cost to recipient: Python + Node present, one ~couple-minute first build, one terminal command. Everything after first launch is in-app.

## Dev vs packaged — one codebase, two modes

Detected at runtime via `sys.frozen`; the TDD loop is unchanged.

| | Dev (daily) | Packaged (`Atlas.app`) |
|---|---|---|
| Frontend | vite dev `:5173` (hot reload) | pre-built `dist`, served by FastAPI |
| Backend | `uvicorn --reload :8000` | uvicorn in a thread, ephemeral local port |
| Window | browser tab | native pywebview window |
| Config | `backend/.env` | `config.json` + Keychain |

`desktop/launcher.py` is exercised only in packaged mode; `cd backend && pytest` and `npm run dev` stay as-is.

## Testing

- **Backend TDD-first against `FakeServiceNow`** (CLAUDE.md). New `/api/settings`, `/oauth/callback`, `/api/test-connection`, `/api/status` routes get failing-test-first coverage.
- **`paths.py` / settings-source resolution** — pure logic; unit-tested both ways (frozen vs dev) by faking `sys.frozen`. No bundle needed.
- **Launcher** (port-pick, health-wait, server start/stop) — unit-tested headless; actual window-open is a thin smoke step (GUI, not unit-tested).
- **`install.sh`** — shellcheck in CI + documented manual smoke on a clean machine. Existing GitHub Actions (pytest + frontend build) keep gating.

## Guardrails & risks

- **#1 no corporate data on personal Mac** — dev still runs `USE_FAKE`/mocks; packaged real-instance use happens on each user's own sanctioned Mac. ✅
- **#2 secrets never in repo** — secrets only in Keychain; `config.json` (non-secret) lives outside the repo. ✅
- **frontend calls only `/api`** — relative, served same-origin by FastAPI. ✅
- **#5 schema mirrors CSM/PPM** — untouched. ✅
- **#6 AI additive / deterministic core** — untouched; this is packaging. ✅
- **New risk R5 — shared distribution broadens the compliance surface** (other users' corporate data + tenants flow through Atlas). User owns it like R1; in-app setup keeps it visible. Add to the CLAUDE.md named-risks table.

## Out of scope (deferred)

- Apple Developer ID signing/notarization and a download-and-run `.dmg`/`.pkg`.
- Automated remote provisioning of the Atlas scoped app onto users' ServiceNow instances (in-app instructions only for now).
- M365/email connect flow internals (P2; the Settings page reserves a slot, same OAuth shape).
- Windows/Linux packaging.
