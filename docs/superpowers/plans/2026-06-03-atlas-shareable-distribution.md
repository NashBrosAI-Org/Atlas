# Atlas Shareable Distribution (Plan C) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Atlas hand-to-a-colleague shareable — a one-command installer that builds and installs `Atlas.app` to `~/Applications` (no Apple Developer ID, no Gatekeeper override), plus in-app setup instructions covering the one thing the app can't do for them (install the Atlas scoped app on *their* ServiceNow instance), plus a SHARING guide and the named compliance risk (R5).

**Architecture:** A thin `scripts/install.sh` (Path 1 — local build) delegates the build to the existing `scripts/build-desktop.sh`, then copies `dist/Atlas.app` into `~/Applications`. Because the bundle is *built on the recipient's machine*, it carries no quarantine flag and launches without an Apple Developer ID. An in-app **Help / Setup** React view (reachable from the nav, shown on first run alongside Settings) walks the user through connecting. A `docs/SHARING.md` covers getting the repo + prerequisites. Risk **R5** is recorded in CLAUDE.md.

**Tech Stack:** bash + shellcheck, React/Vite, existing PyInstaller build (`build-desktop.sh`), markdown docs.

**Builds on:** Plan A (desktop shell, `build-desktop.sh` → `Atlas.app`) and Plan B (in-app Settings). This plan is the last of the three.

## Scope boundaries
- **In scope:** `scripts/install.sh`; in-app Help/Setup view; `docs/SHARING.md`; risk R5 in CLAUDE.md; PROGRESS D15.
- **Out of scope:** Apple Developer ID signing/notarization; a downloadable `.dmg`/`.pkg`; automated remote provisioning of the Atlas scoped app onto a user's instance (we give *instructions*, not automation); the app `.icns` icon (needs a design asset — not available); CI build of the packaged binary (heavier infra); M365 (P2).

**Assumed working dir:** the worktree root `/Users/nick/Atlas/.claude/worktrees/desktop-app` (`$REPO`). Backend venv at `$REPO/backend/.venv`. Note: this repo's `CLAUDE.md` to edit is the worktree copy at `$REPO/CLAUDE.md` (a tracked file), NOT the user's global one.

---

## File structure

| File | New/Mod | Responsibility |
|---|---|---|
| `scripts/install.sh` | Create | Path-1 installer: preflight Node → build via `build-desktop.sh` → copy `Atlas.app` to `~/Applications` → open |
| `frontend/src/HelpView.tsx` | Create | In-app Setup/Help: prerequisites + connect steps + ServiceNow scoped-app guidance |
| `frontend/src/App.tsx` | Modify | Add "Help" to the `View` union + nav button; render `HelpView` |
| `docs/SHARING.md` | Create | How to get the repo, prerequisites, install, what each user needs |
| `CLAUDE.md` | Modify | Add risk **R5** to the named-risks table |
| `docs/PROGRESS.md` | Modify | Record Plan C (decision **D15**) |

---

## Task 0: Baseline

- [ ] **Step 1:** `cd "$REPO/backend" && ./.venv/bin/python -m pytest -q` → all pass (52). `cd "$REPO" && ./backend/.venv/bin/python -m pytest desktop/tests -q` → 6. If red, STOP.

---

## Task 1: `scripts/install.sh` (Path 1 installer)

**Files:** Create `scripts/install.sh`

- [ ] **Step 1: Write the script** — `scripts/install.sh`:
```bash
#!/usr/bin/env bash
# Atlas installer (macOS). Builds Atlas.app from THIS checkout and installs it to
# ~/Applications. No Apple Developer ID needed: building locally means macOS
# trusts the result (no Gatekeeper quarantine). Run from a checkout of the repo:
#   bash scripts/install.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

echo "==> Atlas installer (macOS)"

# Node is needed for the frontend build (build-desktop.sh runs `npm ci`).
if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js is required. Install it from https://nodejs.org (or 'brew install node')." >&2
  exit 1
fi

# Build dist/Atlas.app. build-desktop.sh selects a PyInstaller-compatible Python
# (3.10-3.13) and errors clearly if none is present.
bash scripts/build-desktop.sh

# Install into the user's Applications folder.
DEST="$HOME/Applications"
mkdir -p "$DEST"
rm -rf "$DEST/Atlas.app"
cp -R "$REPO/dist/Atlas.app" "$DEST/Atlas.app"

echo "==> Installed: $DEST/Atlas.app"
open "$DEST/Atlas.app"
echo "==> Launched. Find Atlas anytime in ~/Applications (or via Spotlight)."
echo "==> Next: in Atlas, open Help for setup, then Settings to connect your ServiceNow instance."
```

- [ ] **Step 2: Make executable + lint:**
```bash
cd "$REPO"
chmod +x scripts/install.sh
bash -n scripts/install.sh && echo "syntax ok"
command -v shellcheck >/dev/null && shellcheck scripts/install.sh || echo "(shellcheck not installed; skipping)"
```
Expected: `syntax ok`; shellcheck clean (fix any issues) or skipped.

- [ ] **Step 3: Commit**
```bash
cd "$REPO"
git add scripts/install.sh
git commit -m "build: scripts/install.sh — one-command local install to ~/Applications"
```

---

## Task 2: In-app Setup / Help view

**Files:** Create `frontend/src/HelpView.tsx`; Modify `frontend/src/App.tsx`

- [ ] **Step 1: Create `frontend/src/HelpView.tsx`:**
```tsx
export function HelpView() {
  return (
    <div className="help" style={{ padding: 16, maxWidth: 720, fontFamily: "system-ui", lineHeight: 1.5 }}>
      <h2>Setting up Atlas</h2>
      <p>
        Atlas runs entirely on your Mac and talks to your own ServiceNow instance. Nothing is
        hosted anywhere. Follow these steps once to connect it.
      </p>

      <h3>1. Install the Atlas app on your ServiceNow instance</h3>
      <p>
        Atlas reads and writes a set of custom tables that live in a ServiceNow scoped app.
        That app has to be installed on <em>your</em> instance first — Atlas can't create it
        remotely. You'll need admin on the instance.
      </p>
      <ul>
        <li>Deploy the Fluent app in <code>servicenow/</code> with the ServiceNow SDK
            (<code>now-sdk install</code>), or import it as an update set.</li>
        <li>This is a one-time step per instance. Ask whoever shared Atlas with you for the
            app package if you don't have the <code>servicenow/</code> source.</li>
      </ul>

      <h3>2. Create (or pick) a ServiceNow user for Atlas</h3>
      <p>
        Atlas signs in with basic auth. Use a user that is <strong>not</strong> MFA-enrolled
        and has access to the Atlas tables. A dedicated integration-style user is cleanest.
      </p>

      <h3>3. Connect in Settings</h3>
      <p>
        Open <strong>Settings</strong> and enter your instance URL, username, and password,
        then <strong>Test connection</strong>. Your password is stored in the macOS Keychain —
        never in a file. Turn off <em>“Try with demo data”</em> once you're connected.
      </p>

      <h3>Just exploring?</h3>
      <p>
        Leave <em>“Try with demo data”</em> on in Settings — Atlas works fully against built-in
        sample data with no instance required.
      </p>

      <h3>Updating Atlas</h3>
      <p>
        Re-run <code>bash scripts/install.sh</code> from the source folder; it rebuilds and
        replaces the app in <code>~/Applications</code>.
      </p>
    </div>
  );
}
```

- [ ] **Step 2: Wire into `frontend/src/App.tsx`.** Make these exact edits to the existing file:
  1. Add the import after the `SettingsView` import:
     ```tsx
     import { HelpView } from "./HelpView";
     ```
  2. Extend the `View` union to include `"help"`:
     ```tsx
     type View = "now" | "clients" | "dossier" | "settings" | "help";
     ```
  3. Add a Help nav button after the Settings button:
     ```tsx
     <button onClick={() => setView("help")}>Help</button>
     ```
  4. Render it alongside the other views (after the `settings` block):
     ```tsx
     {view === "help" && <HelpView />}
     ```

- [ ] **Step 3: Build to verify:**
```bash
cd "$REPO/frontend" && npm run build
```
Expected: tsc + vite succeed.

- [ ] **Step 4: Commit**
```bash
cd "$REPO"
git add frontend/src/HelpView.tsx frontend/src/App.tsx
git commit -m "feat: in-app Help/Setup view (ServiceNow scoped-app + connect steps)"
```

---

## Task 3: `docs/SHARING.md`

**Files:** Create `docs/SHARING.md`

- [ ] **Step 1: Create `docs/SHARING.md`:**
```markdown
# Sharing Atlas

Atlas is a local macOS app: a FastAPI backend + React UI packaged into `Atlas.app`,
talking to *your own* ServiceNow instance. There is no server to host. Sharing it
means giving someone the source and having them build it locally (which is also why
no Apple Developer ID is needed — a locally built app isn't quarantined by Gatekeeper).

## What a recipient needs

- **macOS** with **Node.js** and a **Python 3.10–3.13** (PyInstaller doesn't support 3.14).
  `brew install node python@3.12` covers both.
- A copy of this repository (git clone if they have access, or a zip of the source).
- Their own **ServiceNow instance** with the **Atlas scoped app installed** (see the in-app
  Help screen) — only required to use real data; demo mode needs nothing.

## Install (one command)

From the repository folder:

```bash
bash scripts/install.sh
```

This builds `Atlas.app` on their machine and installs it to `~/Applications`, then opens it.
Because it's built locally, macOS launches it with no "unidentified developer" prompt.
Re-run the same command to update.

## First run

Atlas opens on demo data. To connect a real instance, follow the in-app **Help** screen:
install the Atlas scoped app on the instance, then enter the instance URL + a (non-MFA)
username + password in **Settings** and **Test connection**. The password is stored in the
macOS Keychain.

## Heads-up (compliance)

Routing another organisation's email/meeting/ServiceNow content through Atlas broadens the
data-handling surface. Each user owns that with their own IT (see risk R5 in CLAUDE.md).
```

- [ ] **Step 2: Commit**
```bash
cd "$REPO"
git add docs/SHARING.md
git commit -m "docs: add SHARING.md (install + per-user prerequisites)"
```

---

## Task 4: Record risk R5 in CLAUDE.md

**Files:** Modify `CLAUDE.md` (the worktree copy at `$REPO/CLAUDE.md`)

- [ ] **Step 1:** In `CLAUDE.md`, find the named-risks table (under `### Named risks (keep current)`) ending with the R4 row:
```
| R4 | Work-laptop proxy may block `*.service-now.com` / Graph | Recon before go-live |
```
Add a new row immediately after it:
```
| R5 | Shared distribution broadens the compliance surface (other users' corporate data + tenants flow through Atlas) | Each user owns it with their IT, like R1; in-app Help + SHARING.md keep it visible |
```

- [ ] **Step 2: Commit**
```bash
cd "$REPO"
git add CLAUDE.md
git commit -m "docs: add risk R5 (shared distribution compliance surface)"
```

---

## Task 5: Build, smoke-test, document

- [ ] **Step 1: Verify full suites still green** (no code logic changed, but confirm):
```bash
cd "$REPO/backend" && ./.venv/bin/python -m pytest -q
cd "$REPO" && ./backend/.venv/bin/python -m pytest desktop/tests -q
```

- [ ] **Step 2: Smoke-test the installer end to end** (it installs to `~/Applications`; we verify then clean up):
```bash
cd "$REPO"
bash scripts/install.sh
ls -d "$HOME/Applications/Atlas.app" && echo "installed ✅"
# confirm it launches + serves (find Atlas's own port; do NOT trust the first loopback port):
sleep 6
port=$(lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -E "^Atlas" | grep -oE '127\.0\.0\.1:[0-9]+' | head -1 | cut -d: -f2)
echo "Atlas port=$port"
[ -n "$port" ] && curl -s -o /dev/null -w "GET / -> %{http_code}\n" "http://127.0.0.1:$port/"
[ -n "$port" ] && curl -s -o /dev/null -w "GET /api/status -> %{http_code}\n" "http://127.0.0.1:$port/api/status"
# cleanup the smoke install:
pkill -f "Atlas.app/Contents/MacOS/Atlas" 2>/dev/null || true
rm -rf "$HOME/Applications/Atlas.app" && echo "smoke install removed"
```
Expected: `installed ✅`, both curls `200`, then cleaned up. (Open the in-app **Help** and **Settings** tabs once manually to eyeball the Help content if you want.)

- [ ] **Step 3: PROGRESS.md** — add decision **D15**:
```markdown
**D15 — Shareable distribution (Plan C).** `scripts/install.sh` builds `Atlas.app`
locally (via `build-desktop.sh`) and installs it to `~/Applications` — no Apple
Developer ID, no Gatekeeper override, because a locally built bundle isn't
quarantined. In-app **Help** view + `docs/SHARING.md` walk a recipient through
prerequisites (Node + Python 3.10–3.13), getting the source, installing the Atlas
scoped app on their instance, and connecting in Settings. Risk **R5** (shared
distribution broadens the compliance surface) added to CLAUDE.md. Completes the
desktop trilogy (A shell, B in-app config, C distribution).
Plan: `docs/superpowers/plans/2026-06-03-atlas-shareable-distribution.md`.
```
Also update the "Current status" / Desktop line to note Plan C complete.

- [ ] **Step 4: Commit**
```bash
cd "$REPO"
git add docs/PROGRESS.md
git commit -m "docs: record shareable distribution (D15)"
```

---

## Done criteria
- `scripts/install.sh` builds + installs `Atlas.app` to `~/Applications` and it serves (smoke 200s); shellcheck/`bash -n` clean.
- In-app **Help** tab renders the setup steps; `npm run build` clean.
- `docs/SHARING.md` present; risk **R5** in CLAUDE.md; PROGRESS D15.
- Full test suites still green (52 + 6).

## Self-review checklist (run after writing)
- Spec coverage: installer ✅, in-app setup instructions ✅ (explicit user requirement), SN scoped-app guidance ✅, SHARING guide ✅, R5 ✅. Icon + CI-smoke explicitly out of scope (noted).
- No placeholders: install.sh, HelpView.tsx, SHARING.md, and the R5 row are concrete. App.tsx edits are exact (file is small; the four edits match its current structure).
- Consistency: the `View` union edit matches `App.tsx`; install.sh delegates to the real `build-desktop.sh`; the smoke test uses the robust `^Atlas` port detection (NOT the first loopback port, which can be Dropbox's 17600).
