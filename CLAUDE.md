# CLAUDE.md — Atlas

Project guardrails and conventions for anyone (human or agent) working in this repo. Read the
**Hard rules** before changing anything; they override convenience.

## What Atlas is
A client-centric command center for juggling ~6 customer accounts. **ServiceNow scoped app** =
backend/system-of-record. The daily UI is a **native macOS desktop app** (`Atlas.app`): a FastAPI
backend serving a React UI from **one** local process, wrapped in a native window
(pywebview + PyInstaller) — not a ServiceNow Workspace, not a browser tab. It's configured entirely
in-app (a Settings page; password → Keychain, non-secrets → `~/Library/Application Support/Atlas/`)
and installed with `scripts/install.sh` (local build, no Apple Developer ID). In dev it still runs as
FastAPI (`:8000`) + Vite (`:5173`). Microsoft 365 (email/calendar) and AI (summaries, decks, search)
layer on in later phases. Full picture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

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
| R5 | Shared distribution broadens the compliance surface (other users' corporate data + tenants flow through Atlas) | Each user owns it with their IT, like R1; in-app Help + SHARING.md keep it visible |

## Conventions

**Workflow & git** (per the user's global WORKFLOW.md)
- Branch naming: `feature/…`, `fix/…`, `chore/…` (kebab-case). Never commit straight to `main`.
- Commit messages: one line, present-tense imperative ("add Now ordering").
- Open a PR; merge once CI is green — `gh` CLI or GitHub MCP, whichever has `NashBrosAI-Org` access (`gh` is reliable; the MCP token currently lacks org access). Never blind-merge on red/pending CI. Tests pass and no debug code before merging.

**Concurrent sessions — one worktree each**
> **Session start (do this first, automatically — do not ask):** the moment a session is going to
> make *any* edit, put it in its own worktree *before touching a file* — `claude --worktree <task>`
> or the `EnterWorktree` tool. **Never edit the primary `main` checkout directly.** This is
> mandatory and automatic; treat it as the first step of every non-trivial task, not a prompt for
> the user. (Three merge conflicts in one session traced to skipping this — see D8/D10.)

**Worktrees are the default unit of work, not just a concurrency tool.** Every non-trivial task gets
its own worktree (which carries its own branch); the primary checkout stays clean on `main` as the
deploy base and never holds in-progress work. The only exception is trivial read-only work
(questions, code review), which needs no branch or worktree.

Branches isolate *commits*, not the working directory: two sessions sharing one checkout also
share the index, stash, and `HEAD`, so one session's `git add -A`/`commit`/`reset`/branch-switch
can scoop up or clobber the other's uncommitted work. A worktree gives each task its own directory
*and* branch, so collisions are structurally impossible. Start one isolated with
`claude --worktree <short-desc>`, or by hand:
```bash
git worktree add ../atlas-<task> -b <prefix>/<short-desc> origin/main
# work, commit, push, open + merge the PR from that folder, then from the primary checkout:
git worktree remove ../atlas-<task>
```
Background agents auto-isolate (`worktree.bgIsolation`); **interactive** sessions do not — isolate
them with the commands above. Canonical rule (applies to every repo, not just this one):
[`~/.claude/WORKFLOW.md`](file:///Users/nick/.claude/WORKFLOW.md) → "Concurrent sessions — one worktree each".

**Python (backend)**
- FastAPI + pydantic v2; endpoints are `async`. Python 3.11+ target.
- **All ServiceNow access goes through the `ServiceNowClient` interface** (`app/servicenow.py`);
  `get_sn` (`app/main_deps.py`) is the single DI seam, overridden in tests. No ad-hoc SN clients.
- Routers stay thin: validate (pydantic models in `app/models.py`) → call the client. Cross-record
  logic (ordering, prep assembly) lives in named helpers, not inline magic.
- **TDD:** failing test first, against `FakeServiceNow`. `pytest` (`asyncio_mode=auto`).

**TypeScript / React (frontend)**
- `src/types.ts` mirrors the backend pydantic models — change both together.
- The frontend calls **only** the relative `/api` — same-origin when packaged (FastAPI serves the
  built bundle); a Vite dev proxy forwards `/api` → `:8000` in `npm run dev`. No direct SN/Graph
  calls, no secrets in the client. Small, focused view files.

**ServiceNow (scoped app)**
- Built as **Fluent code via the ServiceNow SDK** (`now-sdk`), *not* hand-built in the UI. The app
  lives in `servicenow/`; deploy with `now-sdk install` to `nnash.service-now.com` (Zurich, MFA on).
- `now-sdk auth` is interactive (OAuth code-paste) — run it in a real/integrated terminal (e.g. VS
  Code), not a background runner. Table/field names follow `docs/DATA-MODEL.md`, CSM/PPM-aligned (rule #5).

**General**
- One responsibility per file; keep files small enough to hold in context.
- **Update [docs/PROGRESS.md](docs/PROGRESS.md) after each unit of work**, not at session end.
  Record significant decisions in its **Decisions** log.

## Docs index
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — tiers, data flow, phasing
- [docs/DATA-MODEL.md](docs/DATA-MODEL.md) — Client-centric schema
- [docs/PROGRESS.md](docs/PROGRESS.md) — status tracker + **decision log (ADR-style)**
- [docs/BACKLOG.md](docs/BACKLOG.md) — queued feature ideas / gaps (lighter than the phase roadmap)
- [docs/components/](docs/components/) — per-component charters (each with its own guardrails)
- [docs/superpowers/plans/](docs/superpowers/plans/) — implementation plans

## Run / test
```bash
# backend (against the mock — no live instance needed)
cd backend && source .venv/bin/activate && pytest -v
USE_FAKE=true uvicorn app.main:app --reload --port 8000
# frontend (separate terminal; needs backend on :8000)
cd frontend && npm run dev

# desktop app — build & install a native Atlas.app to ~/Applications (re-run to update)
bash scripts/install.sh          # builds + installs + opens (needs Node + Python 3.10–3.13)
bash scripts/build-desktop.sh    # just build dist/Atlas.app without installing
```
