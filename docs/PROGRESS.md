# Atlas — Progress Tracker

Update this **after each unit of work**, not at session end. (Per the user's standing
preference for living progress docs.)

Last updated: 2026-06-02 (worktree rule enshrined in CLAUDE.md; MCP diagnosis)

## Current status
- **Phase:** P1 (SN-backed command center foundation) — **Plans 1 & 2 code complete**; now wiring the **real ServiceNow instance** via the SDK.
- **Plans done:** [`superpowers/plans/2026-06-02-atlas-foundation.md`](superpowers/plans/2026-06-02-atlas-foundation.md) (Plan 1), [`superpowers/plans/2026-06-02-atlas-dossier.md`](superpowers/plans/2026-06-02-atlas-dossier.md) (Plan 2).
- **Branch:** `main` (canonical). **Remote: `NashBrosAI-Org/Atlas` (private)**, pushed 2026-06-02. **CI:** GitHub Actions (backend pytest + frontend build) — green.
- **Next (in VS Code):** authenticate the ServiceNow SDK to `nnash`, then provision the scoped app + 14 tables as Fluent code and `install` it. See **"ServiceNow provisioning"** below — that's the live pickup point.

## Plan 1 task status — COMPLETE (code)
| Task | What | Status | Where it runs |
|------|------|--------|---------------|
| 1–6 | ServiceNow scoped app + full 14-table schema | 🔄 **superseded** — now built as Fluent code via the SDK (see below), not by hand | ServiceNow (`nnash`) |
| 7–13 | FastAPI backend (config, models, ServiceNowClient + FakeServiceNow, HttpServiceNow + OAuth, DI, Clients/Tasks API, deterministic Now ordering) | ✅ done | personal Mac |
| 14 | React Now view | ✅ done | personal Mac |
| 15 | Point app at live instance + verify | ⏳ TODO — after the SDK provision lands | personal Mac → `nnash` |

## Plan 2 task status — COMPLETE (code)
Generic `crud_router` factory (Contact/Engagement/Theme/Meeting/Transcript/Note), polymorphic Note pinning, `GET /api/clients/{id}/dossier` aggregate, React dossier page + org chart + transcript paste + note composer. **30/30 backend tests green; frontend builds clean; dossier verified e2e against the mock.**

## ServiceNow provisioning — the proper "app-as-code" path (PICK UP HERE in VS Code)

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

## Next plans (after the instance is live)
- **Plan 3 — Awareness:** Activity timeline, stale-client radar, Links, Tags, KeyDates + reminders, scheduled export/backup job.
- **Plan P2 — M365:** Entra recon → email + calendar, email→task, auto-association, meeting-prep assembler, morning briefing.
- **Plan P3 — AI & decks:** Anthropic summaries/drafting/prioritization, RAG search, `.pptx` + web decks on official ServiceNow brand kit.
