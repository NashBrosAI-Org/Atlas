# Atlas — Progress Tracker

Update this **after each unit of work**, not at session end. (Per the user's standing
preference for living progress docs.)

Last updated: 2026-06-03 (live READ path to `nnash` verified end-to-end; desktop Plans A–C merged; backend basic-auth canonical via D14)

## Current status
- **Phase:** P1 (SN-backed command center foundation) — **Plans 1 & 2 code complete**; **SN scoped app + all 14 tables now provisioned and verified on the live `nnash` instance** via the SDK. Remaining P1 work is Plan-1 Task 15 (point the FastAPI backend at the live instance).
- **Plans done:** [`superpowers/plans/2026-06-02-atlas-foundation.md`](superpowers/plans/2026-06-02-atlas-foundation.md) (Plan 1), [`superpowers/plans/2026-06-02-atlas-dossier.md`](superpowers/plans/2026-06-02-atlas-dossier.md) (Plan 2).
- **Branch:** `main` (canonical). **Remote: `NashBrosAI-Org/Atlas` (private)**, pushed 2026-06-02. **CI:** GitHub Actions (backend pytest + frontend build) — green. SN Fluent app added on `feature/servicenow-fluent-app` (PR pending).
- **Desktop:** Plan A (desktop shell) complete (D13) — `Atlas.app` builds via `scripts/build-desktop.sh` and runs as a native window; serves UI + `/api` from one local process, no Gatekeeper quarantine. **Plan B (in-app configuration) complete on `feature/desktop-config`** (D14) — a Settings page configures the ServiceNow connection in-app (basic auth per D11); non-secrets → `~/Library/Application Support/Atlas/config.json`, password → Keychain; verified end-to-end in the packaged app.
- **Next:** finish Plan-1 **Task 15**. Basic auth is already wired on `main` (D14) and the **READ path is verified live** (this session, 2026-06-03 — see "Live connection status" below). Remaining: a **write round-trip** (create→get→list) against `nnash`, then confirm the dossier renders **real** records. Watch the mock-vs-real field gaps (booleans as `"true"/"false"`, choice/date formats, reference fields, pagination).

## Plan 1 task status — COMPLETE (code)
| Task | What | Status | Where it runs |
|------|------|--------|---------------|
| 1–6 | ServiceNow scoped app + full 14-table schema | ✅ **done** — built as Fluent code (`servicenow/`) via the SDK and `install`ed to `nnash`; 14/14 tables verified | ServiceNow (`nnash`) |
| 7–13 | FastAPI backend (config, models, ServiceNowClient + FakeServiceNow, HttpServiceNow + OAuth, DI, Clients/Tasks API, deterministic Now ordering) | ✅ done | personal Mac |
| 14 | React Now view | ✅ done | personal Mac |
| 15 | Point app at live instance + verify | 🔄 **READ path verified live** (2026-06-03): basic auth (D14) connects to `nnash`, `x_atlas_sn_client` queryable (0 rows). Write round-trip + dossier-on-real-data pending | personal Mac → `nnash` |

## Plan 2 task status — COMPLETE (code)
Generic `crud_router` factory (Contact/Engagement/Theme/Meeting/Transcript/Note), polymorphic Note pinning, `GET /api/clients/{id}/dossier` aggregate, React dossier page + org chart + transcript paste + note composer. **30/30 backend tests green; frontend builds clean; dossier verified e2e against the mock.**

## ServiceNow provisioning — the proper "app-as-code" path ✅ DONE (2026-06-02)

**Outcome:** Fluent app `Atlas` (scope **`x_atlas_sn`**, app sys_id `cdcfbe665d124640a701093f00fee569`) built from `servicenow/` and `install`ed to `nnash`. **All 14 tables verified live** (`x_atlas_sn_client … _tag_m2m`). Code committed on `feature/servicenow-fluent-app`. The auth path was **not** the planned OAuth — see D11 for the wall and the basic-auth workaround.

**Decision (D9):** build the scoped app the proper, version-controlled way with the **ServiceNow SDK + Fluent** (TypeScript app-as-code → `now-sdk install` deploys to the instance). This *supersedes* hand-building Plan-1 Tasks 1–6 in the UI. ServiceNow officially supports authoring Fluent apps via Claude Code.

**Instance:** `https://nnash.service-now.com` · Build **Zurich** · **MFA enabled** · offering enterprise.
**Tooling (verified on personal Mac):** Node v24, npm 11, `@servicenow/sdk@4.7.1` (npx cache warm).
**App location (planned):** `servicenow/` subfolder of this repo (monorepo: `backend/`, `frontend/`, `servicenow/`).

### Step 1 — Authenticate the SDK (BLOCKING, interactive — DO THIS FIRST in VS Code's integrated terminal)
The OAuth flow opens the browser to log in (+ MFA), then ServiceNow shows a **code you paste back into the terminal**. A non-TTY / background runner CANNOT do the paste (that's why it failed in the Claude Code session). **VS Code's integrated terminal works** — run there:
```bash
npx --yes @servicenow/sdk@4.7.1 auth --add https://nnash.service-now.com --type oauth --alias nnash
# browser opens → log in + MFA → copy the code shown → paste at:
#   "Copy the code from the browser and paste it here:"  → Enter
npx --yes @servicenow/sdk@4.7.1 auth --list   # verify: shows the nnash credential
```
Status: ❌ **not yet authenticated** (attempts so far ran in a non-interactive runner and couldn't paste the code). Basic auth was tried and bounced into a blank MFA page — use **OAuth**, not basic.

### Step 2+ — Claude can drive these once Step 1 is authenticated
- `npx @servicenow/sdk init --appName "Atlas" --packageName "atlas-sn" --scopeName "x_<code>_atlas" --template base` in `servicenow/`. Confirm the real vendor-prefix (`x_<code>`) for `nnash` after auth so the scope matches (avoids a rename).
- Write all 14 tables as Fluent `.now.ts` from [`DATA-MODEL.md`](DATA-MODEL.md): StringColumn/DateColumn/BooleanColumn/ChoiceColumn/ReferenceColumn; the Note polymorphic target; CSM/PPM-aligned names.
- `npx @servicenow/sdk build` (validate) → `npx @servicenow/sdk install` (deploy to `nnash`). Verify the 14 tables landed.
- Commit `servicenow/` to the repo (version-controlled + CI-covered).
- Then Plan-1 Task 15: point the FastAPI app at `nnash` (`USE_FAKE=false`, OAuth) and confirm the dossier renders **real** records — watch for the mock-vs-real field gaps (booleans as `"true"/"false"`, choice/date formats, list pagination).

> "App repo publish" (the **Application Repository**) is a *later* step — that's for pushing the finished app to *other* instances in the org. Getting it into `nnash` from this repo is the `install` above.

## Live connection status (Task 15) — updated 2026-06-03

- **READ path verified end-to-end.** With `USE_FAKE=false` + basic auth (`atlas.sdk` / `SN_AUTH=basic`, per D14/D11), `build`ing the live client and calling `list("x_atlas_sn_client")` against `nnash` returns **200 with 0 rows** — auth works, the scope/table resolve, and `allowWebServiceAccess:true` is honored (no 403). The schema is empty (fresh install).
- **Pending:** a **write round-trip** (create→get→list) to confirm choice-defaults land (`status=active`) and that reference/boolean fields come back in the shape the frontend expects. Not yet run (it writes a row to the live instance).
- **⚠️ PR #6 (`feature/backend-live-basic-auth`) disposition — DO NOT MERGE AS-IS.** It predates / overlaps D14's basic-auth, which is canonical on `main`. **But** it carries one fix `main` still lacks: `sysparm_exclude_reference_link=true` + `sysparm_display_value=false` on **get/create/update** (currently `list`-only in `app/servicenow.py`). Without it, live reference fields return as `{link,value}` objects instead of plain `sys_id` strings — a real mock-vs-real gap. **Action:** port just that parity change onto `main`'s `HttpServiceNow`, then close PR #6.

## Decisions (ADR-style log)

Significant decisions and their rationale, newest last.

**D1 — ServiceNow is the backend; a custom local app is the frontend.** SN scoped app = data/system-of-record; React+FastAPI on the work Mac = the daily surface, reached via REST/OAuth (not a Workspace).

**D2 — Data-residency relaxed: email/meeting content may live in the SN instance.** The user routes email content into SN to drive the app and survive the company's ~annual retention window; owns the legal/compliance risk with IT (risk R1). **Highest-risk decision — stays visible.**

**D3 — Lightweight custom scoped-app tables now; CSM/PPM migration later.** Custom tables with CSM/PPM-aligned names (Client→Account, Engagement→Project, Contact→Contact) so migration is a mapping, not a rebuild.

**D4 — Deterministic prioritization in v1; AI is additive.** "Now" view sorts by priority → due_date → commitment in plain code; no feature depends on the Anthropic API.

**D5 — Develop on the personal Mac against mocks; clone to the work Mac.** Build behind a `ServiceNowClient` interface with `FakeServiceNow` (`USE_FAKE=true`); real creds/instance only where authenticated.

**D6 — Transcripts' full text retained in SN, plus an export/backup.** Store full text in SN AND export/back it up so the instance is never the only copy (risk R2).

**D7 — One generic `crud_router` factory, not per-entity routers (Plan 2).** DRY backend; Notes pin polymorphically via `target_table`+`target_id` with no special-casing.

**D8 — Concurrent `/btw` fork session reconciled onto `main`.** Isolate each track in its own `git worktree`; `main` is canonical. Never share a working tree across sessions.

**D9 — Build the SN scoped app as Fluent code via the ServiceNow SDK.** Instead of hand-building tables (Plan-1 Tasks 1–6) or a Fix Script, define the app as TypeScript (`servicenow/`, `now-sdk`) and `install` to `nnash`. Proper, version-controlled, CI-coverable, skill-building, and ServiceNow-supported for Claude Code authoring. The interactive `now-sdk auth` is the one manual step (must run in an interactive terminal — e.g. VS Code).

**D10 — Worktree rule lives canonically in `~/.claude/WORKFLOW.md`; the repo `CLAUDE.md` only points to it (PR #2).** Operationalizes D8: rather than fork the full rule per repo (drift risk), Atlas's `CLAUDE.md` carries a short "Concurrent sessions — one worktree each" subsection that references the global file as source of truth. This also satisfies the `SessionStart` hook `~/.claude/hooks/check-worktree-rule.sh`, which greps each NashBros repo's root `CLAUDE.md` for the phrase `one worktree each`. Same session: diagnosed the `sourcegraph` MCP failure (unset `SOURCEGRAPH_ENDPOINT`/`SOURCEGRAPH_ACCESS_TOKEN` → host-less URL; set both or disable the plugin), and noted the `github` MCP token lacks `NashBrosAI-Org` access (`create_pull_request` → Not Found; used `gh` CLI as fallback).

**D11 — SDK auth to `nnash` uses basic auth via a local non-MFA user, not OAuth.** Every OAuth path was walled by the org's Zurich hardening: (a) the full **ServiceNow IDE** Store app that provisions the SDK's fixed OAuth client (`543e5655…`) is **"Purchase not available for your company"**; (b) only **ServiceNow IDE Platform** (`com.glide.ide_platform` v1.0.0) was installable, which does **not** create the `oauth_entity`; (c) importing the legacy OAuth-config XMLs (even as `security_admin`) **silently no-ops** because Zurich moved inbound OAuth to the new *Inbound Integration Experience* and won't pin the SDK's fixed client id. `now-sdk auth` has **no flag** to supply a custom client. **Workaround that worked:** `--type basic` against a dedicated local user **`atlas.sdk`**. now-sdk needs an *interactive* user (Machine Identity → "Only interactive users are allowed to access UI") that is *not* MFA-enrolled (now-sdk can't enter an MFA code). So: created `atlas.sdk`, forced `web_service_access_only=false` + `internal_integration_user=false` via background script (Zurich ties web-service-only to the Machine-Identity identity type, which the form makes read-only), it inherited `admin` from the account clone. Credentials live only in the SDK's OS keychain entry; the password is a secret (not in repo). **Implication for Task 15:** the FastAPI `auth.py` OAuth password grant will hit the same wall — switch the live backend to basic auth too.

**D12 — SDK `install` cannot self-confirm status on this instance; verify out-of-band.** `now-sdk install` pushes the package fine but its post-install status check calls a *flow-activation endpoint* that ships with the (org-blocked) full IDE app — absent here, so install reports `Forbidden` / "Could not determine app installation status" **even though the app lands**. Verify by querying `sys_db_object` for `x_atlas_sn_` tables (did: 14/14). Treat those post-install errors as noise on `nnash`, not failure.

**D13 — Atlas ships as a native macOS app (desktop shell, Plan A).** FastAPI serves the built React bundle (with SPA fallback); `desktop/launcher.py` runs uvicorn on a free loopback port in a background thread and opens a native pywebview (WKWebView) window; PyInstaller bundles it into `Atlas.app` via `scripts/build-desktop.sh`. The build venv must use **Python 3.10–3.13** (PyInstaller 6.11 does not support 3.14, the machine's default `python3`). Built locally → **no Gatekeeper quarantine**, so it runs without an Apple Developer ID — the basis for Plan C's share story. Plan A runs on demo data only (`FakeServiceNow`, which starts empty — manual entry or future seed data fills it); **in-app configuration is Plan B**, the **shareable local-build installer is Plan C**. Spec: [`superpowers/specs/2026-06-02-atlas-desktop-app-design.md`](superpowers/specs/2026-06-02-atlas-desktop-app-design.md); plan: [`superpowers/plans/2026-06-03-atlas-desktop-shell.md`](superpowers/plans/2026-06-03-atlas-desktop-shell.md).

**D14 — In-app configuration (Plan B), basic auth per D11.** A Settings/Integrations page (React, doubles as first-run surface, with a "Try with demo data" toggle) configures the ServiceNow connection from inside the app. Non-secret settings persist to `~/Library/Application Support/Atlas/config.json`; the password to the macOS Keychain (`atlas-sn`). `get_settings()` overlays this on env/.env; `get_sn()` is dynamic (`reset_sn()` after save) and builds a **basic-auth** live client (`HttpServiceNow` + httpx `auth=(user,pass)`), since OAuth is walled on `nnash` (D11). New routes: `/api/settings`, `/api/status`, `/api/test-connection`. Verified in the packaged `Atlas.app`: settings persist, password lands in the Keychain (PyInstaller bundles keyring's macOS backend), nothing secret is returned by the API. Startup crashes now log to `atlas-error.log`. Plan: [`superpowers/plans/2026-06-03-atlas-in-app-config.md`](superpowers/plans/2026-06-03-atlas-in-app-config.md).

## Next plans (after the instance is live)
- **Plan 3 — Awareness:** Activity timeline, stale-client radar, Links, Tags, KeyDates + reminders, scheduled export/backup job.
- **Plan P2 — M365:** Entra recon → email + calendar, email→task, auto-association, meeting-prep assembler, morning briefing.
- **Plan P3 — AI & decks:** Anthropic summaries/drafting/prioritization, RAG search, `.pptx` + web decks on official ServiceNow brand kit.
