# Atlas Desktop Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the existing Atlas FastAPI + React app as a double-clickable native macOS app (`Atlas.app`) that runs as a single local process in a native window, with no browser and no second port.

**Architecture:** Collapse the two-process dev setup into one — FastAPI also serves the *built* React bundle (`frontend/dist`) at `/`, keeping the API under `/api`. A thin `desktop/` launcher starts uvicorn on a free `127.0.0.1` port in a background thread, waits for `/api/health`, then opens a native WKWebView window (pywebview) pointed at it. PyInstaller bundles all of this into `Atlas.app`. This plan ships the *shell* only — it runs on demo data (`USE_FAKE=true`); in-app configuration and shareable distribution are Plans B and C.

**Tech Stack:** FastAPI, Starlette `StaticFiles`/`FileResponse`, uvicorn (programmatic `Server`), pywebview (WKWebView), PyInstaller, Vite/React, pytest + `TestClient`.

**Scope boundaries (deliberately deferred):**
- Per-user config (`config.json`), Keychain secrets, `/api/settings`, OAuth connect, Settings UI → **Plan B**.
- `install.sh`, in-app setup instructions, SN-app guidance, risk R5 → **Plan C**.
- This plan’s packaged app reads config the way the app does today (env/`.env` if present) and otherwise defaults to `USE_FAKE=true`, so it launches and shows demo data with zero setup.

**Conventions this plan follows (from CLAUDE.md):**
- Backend: FastAPI, pydantic v2, thin routers, `pytest` (`asyncio_mode=auto`), TDD failing-test-first.
- Frontend: calls only `…/api`; `src/types.ts` mirrors backend (unchanged here).
- Work happens on branch `feature/desktop-app` in the worktree `/Users/nick/Atlas/.claude/worktrees/desktop-app`.

**Assumed working directory for all commands:** the worktree root
`/Users/nick/Atlas/.claude/worktrees/desktop-app` (call it `$REPO`). The backend Python lives in `$REPO/backend`; its virtualenv is referred to as `$VENV` — create it in Task 0 if absent.

---

## File structure

| File | New/Mod | Responsibility |
|---|---|---|
| `backend/app/static.py` | Create | `mount_frontend(app, dist)` — serve `frontend/dist` at `/` with SPA fallback; no-op if dist absent |
| `backend/app/main.py` | Modify | Call `mount_frontend` at the end (after API routers); resolve dist via `ATLAS_FRONTEND_DIST` env or repo default |
| `backend/tests/test_static.py` | Create | Tests: index served at `/`, SPA fallback, `/api/health` still works, no-op when dist missing |
| `frontend/src/api.ts` | Modify | `BASE = "/api"` (relative, same-origin) |
| `frontend/vite.config.ts` | Modify | Dev proxy `/api` → `http://localhost:8000` so relative paths work in `npm run dev` |
| `desktop/__init__.py` | Create | Make `desktop` a package |
| `desktop/server.py` | Create | `find_free_port()`, `wait_until_ready(probe,…)`, `http_probe(url)`, `ServerThread` |
| `desktop/launcher.py` | Create | `main()`: pick port → start server thread → wait health → open pywebview window |
| `desktop/tests/__init__.py` | Create | Package marker for desktop tests |
| `desktop/tests/test_server.py` | Create | Unit tests for `find_free_port` + `wait_until_ready` (pure logic, no window) |
| `desktop/requirements.txt` | Create | Desktop/build-only deps: `-r ../backend/requirements.txt`, `pywebview`, `pyinstaller` |
| `desktop/Atlas.spec` | Create | PyInstaller recipe → windowed `Atlas.app`, bundles `frontend/dist` |
| `scripts/build-desktop.sh` | Create | Build frontend → ensure build venv → `pyinstaller` → `dist/Atlas.app` |
| `docs/PROGRESS.md` | Modify | Record Plan A completion + decision D11 |

---

## Task 0: Establish a clean baseline

**Files:** none (environment only)

- [ ] **Step 1: Ensure the backend venv exists and deps are installed**

Run:
```bash
cd "$REPO/backend"
python3.11 -m venv .venv 2>/dev/null || python3 -m venv .venv
./.venv/bin/pip install -q -r requirements.txt
```
Expected: completes with no error. Set `VENV=$REPO/backend/.venv` for later steps.

- [ ] **Step 2: Run the existing backend tests to confirm a green starting point**

Run:
```bash
cd "$REPO/backend" && ./.venv/bin/python -m pytest -q
```
Expected: all existing tests pass (the dossier/CRUD suite — ~30 tests, 0 failures). If any fail, STOP and report; do not build on a red baseline.

---

## Task 1: Frontend uses a relative API base (works in dev *and* packaged)

**Files:**
- Modify: `frontend/src/api.ts:2`
- Modify: `frontend/vite.config.ts`

**Why:** Packaged, the UI is served same-origin by FastAPI, so `/api` is correct and `http://localhost:8000` is wrong. In `npm run dev` the UI is on `:5173`, so we add a Vite proxy that forwards `/api` to the backend on `:8000`. After this, the same relative path works in both modes.

- [ ] **Step 1: Point the API base at the relative path**

In `frontend/src/api.ts`, change line 2:
```ts
const BASE = "/api";
```

- [ ] **Step 2: Add the dev proxy to Vite**

Replace `frontend/vite.config.ts` with:
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 3: Verify the frontend still builds**

Run:
```bash
cd "$REPO/frontend" && npm ci && npm run build
```
Expected: build succeeds; `frontend/dist/index.html` and `frontend/dist/assets/` exist.

- [ ] **Step 4: Commit**

```bash
cd "$REPO"
git add frontend/src/api.ts frontend/vite.config.ts
git commit -m "feat: relative /api base + vite dev proxy for desktop packaging"
```

---

## Task 2: FastAPI serves the built React bundle (SPA) with a clean fallback

**Files:**
- Create: `backend/app/static.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_static.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_static.py`:
```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.static import mount_frontend


def _make_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>Atlas</title>")
    (dist / "assets" / "app.js").write_text("console.log('atlas')")
    return dist


def test_mount_serves_index_at_root(tmp_path):
    app = FastAPI()
    assert mount_frontend(app, _make_dist(tmp_path)) is True
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "Atlas" in r.text


def test_mount_serves_real_asset(tmp_path):
    app = FastAPI()
    mount_frontend(app, _make_dist(tmp_path))
    client = TestClient(app)
    r = client.get("/assets/app.js")
    assert r.status_code == 200
    assert "atlas" in r.text


def test_unknown_route_falls_back_to_index(tmp_path):
    app = FastAPI()
    mount_frontend(app, _make_dist(tmp_path))
    client = TestClient(app)
    r = client.get("/clients/abc123")  # client-side route, no such file
    assert r.status_code == 200
    assert "Atlas" in r.text


def test_api_routes_are_not_shadowed_by_fallback(tmp_path):
    app = FastAPI()

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    mount_frontend(app, _make_dist(tmp_path))
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_mount_is_noop_when_dist_missing(tmp_path):
    app = FastAPI()
    assert mount_frontend(app, tmp_path / "does-not-exist") is False
    client = TestClient(app)
    assert client.get("/").status_code == 404
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
cd "$REPO/backend" && ./.venv/bin/python -m pytest tests/test_static.py -q
```
Expected: FAIL — `ModuleNotFoundError: No module named 'app.static'`.

- [ ] **Step 3: Write the minimal implementation**

Create `backend/app/static.py`:
```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_frontend(app: FastAPI, dist: Path) -> bool:
    """Serve a built Vite/React bundle from ``dist`` at ``/``.

    The API routers must already be registered on ``app`` before calling this,
    because the SPA catch-all below is registered last and Starlette resolves
    routes in registration order (earlier explicit ``/api/...`` routes win).

    Returns True if the bundle was mounted, False if ``dist`` has no
    ``index.html`` (e.g. running the API in dev without a build) — in which case
    the app is left untouched.
    """
    dist = Path(dist)
    index = dist / "index.html"
    if not index.is_file():
        return False

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str) -> FileResponse:
        candidate = dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)

    return True
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
cd "$REPO/backend" && ./.venv/bin/python -m pytest tests/test_static.py -q
```
Expected: PASS (5 passed).

- [ ] **Step 5: Wire the mount into the real app**

In `backend/app/main.py`, append at the very end of the file (after all `app.include_router(...)` lines):
```python
import os  # noqa: E402
from pathlib import Path  # noqa: E402
from app.static import mount_frontend  # noqa: E402

_default_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
_dist = Path(os.environ["ATLAS_FRONTEND_DIST"]) if os.environ.get("ATLAS_FRONTEND_DIST") else _default_dist
mount_frontend(app, _dist)
```

- [ ] **Step 6: Run the whole backend suite to confirm nothing regressed**

Run:
```bash
cd "$REPO/backend" && ./.venv/bin/python -m pytest -q
```
Expected: all pass (prior tests + 5 new).

- [ ] **Step 7: Manually confirm the single-process app serves the UI**

Run:
```bash
cd "$REPO/frontend" && npm run build
cd "$REPO/backend" && ATLAS_FRONTEND_DIST="$REPO/frontend/dist" USE_FAKE=true ./.venv/bin/python -m uvicorn app.main:app --port 8000 &
sleep 2
curl -s -o /dev/null -w "GET /            -> %{http_code}\n" http://127.0.0.1:8000/
curl -s -o /dev/null -w "GET /api/health  -> %{http_code}\n" http://127.0.0.1:8000/api/health
curl -s -o /dev/null -w "GET /clients/x   -> %{http_code}\n" http://127.0.0.1:8000/clients/x
kill %1 2>/dev/null || true
```
Expected: all three print `200`.

- [ ] **Step 8: Commit**

```bash
cd "$REPO"
git add backend/app/static.py backend/app/main.py backend/tests/test_static.py
git commit -m "feat: serve built React bundle from FastAPI with SPA fallback"
```

---

## Task 3: Desktop server helpers (port + readiness + threaded uvicorn)

**Files:**
- Create: `desktop/__init__.py`
- Create: `desktop/server.py`
- Create: `desktop/tests/__init__.py`
- Test: `desktop/tests/test_server.py`

**Why split from the launcher:** `find_free_port` and `wait_until_ready` are pure logic and must be unit-tested without opening a GUI window or importing pywebview.

- [ ] **Step 1: Write the failing test**

Create `desktop/__init__.py` (empty) and `desktop/tests/__init__.py` (empty), then create `desktop/tests/test_server.py`:
```python
import socket

from desktop.server import find_free_port, wait_until_ready


def test_find_free_port_returns_bindable_port():
    port = find_free_port()
    assert isinstance(port, int)
    assert 1024 < port < 65536
    # The port is free right now, so we can bind it.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))


def test_wait_until_ready_returns_true_when_probe_succeeds():
    calls = {"n": 0}

    def probe():
        calls["n"] += 1
        return calls["n"] >= 3  # not ready twice, then ready

    slept = []
    ok = wait_until_ready(
        probe, timeout=5.0, interval=0.01,
        sleep=slept.append, now=_fake_clock([0.0, 0.0, 0.0, 0.0]),
    )
    assert ok is True
    assert calls["n"] == 3
    assert len(slept) == 2  # slept after the two not-ready probes


def test_wait_until_ready_times_out():
    ok = wait_until_ready(
        lambda: False, timeout=0.05, interval=0.01,
        sleep=lambda _s: None, now=_fake_clock([0.0, 0.02, 0.04, 0.06]),
    )
    assert ok is False


def _fake_clock(values):
    it = iter(values)
    last = [0.0]

    def now():
        try:
            last[0] = next(it)
        except StopIteration:
            last[0] += 1.0
        return last[0]

    return now
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
cd "$REPO" && ./backend/.venv/bin/python -m pytest desktop/tests/test_server.py -q
```
Expected: FAIL — `ModuleNotFoundError: No module named 'desktop.server'`.

- [ ] **Step 3: Write the minimal implementation**

Create `desktop/server.py`:
```python
"""Run the Atlas FastAPI app in a background thread for the desktop shell.

Pure helpers (`find_free_port`, `wait_until_ready`) are unit-tested; the
threaded uvicorn `ServerThread` is exercised by the launcher and the manual
smoke test.
"""
from __future__ import annotations

import socket
import time
import urllib.error
import urllib.request
from threading import Thread
from typing import Callable

import uvicorn


def find_free_port() -> int:
    """Ask the OS for an unused TCP port on the loopback interface."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def wait_until_ready(
    probe: Callable[[], bool],
    timeout: float = 15.0,
    interval: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
) -> bool:
    """Poll ``probe`` until it returns True or ``timeout`` seconds elapse."""
    deadline = now() + timeout
    while now() < deadline:
        if probe():
            return True
        sleep(interval)
    return False


def http_probe(url: str, timeout: float = 1.0) -> bool:
    """Return True if ``url`` answers with HTTP 200."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (loopback only)
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


class ServerThread:
    """A uvicorn server running in a daemon thread, with a clean stop."""

    def __init__(self, app, host: str = "127.0.0.1", port: int = 8000) -> None:
        self.host = host
        self.port = port
        config = uvicorn.Config(app, host=host, port=port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._thread = Thread(target=self._server.run, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=5)
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
cd "$REPO" && ./backend/.venv/bin/python -m pytest desktop/tests/test_server.py -q
```
Expected: PASS (3 passed). (`uvicorn` is already in `backend/requirements.txt`, so the backend venv can import it.)

- [ ] **Step 5: Commit**

```bash
cd "$REPO"
git add desktop/__init__.py desktop/server.py desktop/tests/__init__.py desktop/tests/test_server.py
git commit -m "feat: desktop server helpers (free port, readiness probe, threaded uvicorn)"
```

---

## Task 4: The launcher — start server, wait, open native window

**Files:**
- Create: `desktop/launcher.py`

**Why no unit test:** `main()` opens a GUI window via pywebview (must run on the macOS main thread) — not unit-testable. Its logic is composed entirely of the Task-3 helpers (already tested) plus a `webview` call verified in the Task 7 smoke test. `webview` is imported lazily so importing this module (and the test suite) never requires the GUI dependency.

- [ ] **Step 1: Write the launcher**

Create `desktop/launcher.py`:
```python
"""Atlas desktop entrypoint.

Starts the FastAPI app on a free loopback port in a background thread, waits
for it to answer /api/health, then opens a native window pointed at it.
Bundled by PyInstaller (see desktop/Atlas.spec) into Atlas.app.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _configure_bundled_paths() -> None:
    """When frozen by PyInstaller, point the backend at the bundled frontend."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bundled_dist = Path(meipass) / "frontend" / "dist"
        os.environ.setdefault("ATLAS_FRONTEND_DIST", str(bundled_dist))
        # Make the bundled `app` package importable.
        sys.path.insert(0, str(Path(meipass) / "backend"))
    else:
        # Running from source: ensure `backend` is importable.
        repo = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(repo / "backend"))


def main() -> int:
    _configure_bundled_paths()

    # Imported after path setup so the bundled/locale backend resolves.
    from app.main import app  # noqa: E402
    from desktop.server import ServerThread, find_free_port, http_probe, wait_until_ready

    port = find_free_port()
    server = ServerThread(app, host="127.0.0.1", port=port)
    server.start()

    ready = wait_until_ready(lambda: http_probe(f"{server.base_url}/api/health"), timeout=20.0)
    if not ready:
        print("Atlas backend failed to start", file=sys.stderr)
        server.stop()
        return 1

    import webview  # lazy: GUI dependency only needed at runtime

    window = webview.create_window("Atlas", server.base_url, width=1280, height=860)
    window.events.closed += server.stop  # stop the server when the window closes
    webview.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Confirm the module imports without the GUI dependency**

Run:
```bash
cd "$REPO" && ./backend/.venv/bin/python -c "import desktop.launcher; print('import ok')"
```
Expected: prints `import ok` (no `webview` required at import time).

- [ ] **Step 3: Commit**

```bash
cd "$REPO"
git add desktop/launcher.py
git commit -m "feat: desktop launcher — threaded server + native pywebview window"
```

---

## Task 5: Packaging recipe (deps + PyInstaller spec)

**Files:**
- Create: `desktop/requirements.txt`
- Create: `desktop/Atlas.spec`

- [ ] **Step 1: Declare desktop/build dependencies**

Create `desktop/requirements.txt`:
```text
# Desktop shell + build tooling. Installs the backend runtime deps plus the
# native-window and packaging libraries. Used by scripts/build-desktop.sh.
-r ../backend/requirements.txt
pywebview==5.4
pyinstaller==6.11.1
```

- [ ] **Step 2: Write the PyInstaller spec**

Create `desktop/Atlas.spec`:
```python
# PyInstaller spec for Atlas.app — build with:  pyinstaller desktop/Atlas.spec
# Run from the repo root so the relative data paths resolve.
import os

from PyInstaller.utils.hooks import collect_submodules

REPO = os.getcwd()

a = Analysis(
    [os.path.join(REPO, "desktop", "launcher.py")],
    pathex=[os.path.join(REPO, "backend"), REPO],
    binaries=[],
    datas=[
        (os.path.join(REPO, "frontend", "dist"), os.path.join("frontend", "dist")),
        (os.path.join(REPO, "backend", "app"), os.path.join("backend", "app")),
    ],
    hiddenimports=(
        collect_submodules("uvicorn")
        + collect_submodules("app")
        + ["desktop.server", "webview"]
    ),
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "_pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Atlas",
    console=False,  # windowed app — no terminal
)
coll = COLLECT(exe, a.binaries, a.datas, name="Atlas")

app = BUNDLE(
    coll,
    name="Atlas.app",
    icon=None,  # placeholder; real .icns added in a later plan
    bundle_identifier="dev.nashops.atlas",
)
```

- [ ] **Step 3: Commit**

```bash
cd "$REPO"
git add desktop/requirements.txt desktop/Atlas.spec
git commit -m "build: desktop deps + PyInstaller spec for Atlas.app"
```

---

## Task 6: One-command local build script

**Files:**
- Create: `scripts/build-desktop.sh`

- [ ] **Step 1: Write the build script**

Create `scripts/build-desktop.sh`:
```bash
#!/usr/bin/env bash
# Build Atlas.app locally from this repo. Produces dist/Atlas.app.
# Requires Python 3.11+ and Node. Run from anywhere; resolves the repo root.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

echo "==> Building frontend"
( cd frontend && npm ci && npm run build )

echo "==> Preparing build venv"
BUILD_VENV="$REPO/.build-venv"
python3.11 -m venv "$BUILD_VENV" 2>/dev/null || python3 -m venv "$BUILD_VENV"
"$BUILD_VENV/bin/pip" install -q --upgrade pip
"$BUILD_VENV/bin/pip" install -q -r desktop/requirements.txt

echo "==> Packaging Atlas.app"
rm -rf build dist
"$BUILD_VENV/bin/pyinstaller" --noconfirm desktop/Atlas.spec

echo "==> Done: $REPO/dist/Atlas.app"
```

- [ ] **Step 2: Make it executable and lint it**

Run:
```bash
cd "$REPO"
chmod +x scripts/build-desktop.sh
command -v shellcheck >/dev/null && shellcheck scripts/build-desktop.sh || echo "(shellcheck not installed; skipping)"
```
Expected: `chmod` succeeds; shellcheck reports no errors (or is skipped).

- [ ] **Step 3: Commit**

```bash
cd "$REPO"
git add scripts/build-desktop.sh
git commit -m "build: scripts/build-desktop.sh — one-command local Atlas.app build"
```

---

## Task 7: Build and smoke-test the real app

**Files:** none (verification + docs)

- [ ] **Step 1: Build Atlas.app**

Run:
```bash
cd "$REPO" && bash scripts/build-desktop.sh
```
Expected: ends with `Done: …/dist/Atlas.app`; `dist/Atlas.app` exists. If PyInstaller reports a missing module at launch (Step 2), add it to `hiddenimports` in `desktop/Atlas.spec` and rebuild.

- [ ] **Step 2: Launch and confirm the window shows Atlas on demo data**

Run:
```bash
open "$REPO/dist/Atlas.app"
```
Expected: a native window titled **Atlas** opens (no browser, no terminal) and renders the Now/Clients UI populated with `FakeServiceNow` demo data. Closing the window exits the app (no lingering process — verify with `pgrep -fl Atlas || echo "no atlas process"`).

- [ ] **Step 3: Confirm it was NOT quarantined (built locally)**

Run:
```bash
xattr -p com.apple.quarantine "$REPO/dist/Atlas.app" 2>&1 | head -1 || echo "no quarantine attribute (expected for a locally built app)"
```
Expected: prints "no quarantine attribute…" — confirming the locally built app needs no Gatekeeper override (the foundation for Plan C’s share story).

- [ ] **Step 4: Confirm the full test suite is green**

Run:
```bash
cd "$REPO/backend" && ./.venv/bin/python -m pytest -q
cd "$REPO" && ./backend/.venv/bin/python -m pytest desktop/tests -q
```
Expected: both suites pass.

- [ ] **Step 5: Update PROGRESS.md**

In `docs/PROGRESS.md`, add under the decision log:
```markdown
**D11 — Atlas ships as a native macOS app (desktop shell).** FastAPI serves the
built React bundle; `desktop/launcher.py` runs uvicorn on a free loopback port
in a thread and opens a native pywebview window; PyInstaller bundles it into
`Atlas.app` (`scripts/build-desktop.sh`). Plan A (shell) runs on demo data;
in-app configuration (Plan B) and the shareable local-build installer (Plan C)
follow. Spec: `docs/superpowers/specs/2026-06-02-atlas-desktop-app-design.md`.
```
And update the "Current status" line to note the desktop shell is complete.

- [ ] **Step 6: Commit**

```bash
cd "$REPO"
git add docs/PROGRESS.md
git commit -m "docs: record desktop shell (D11) in PROGRESS"
```

---

## Task 8: Ignore build artifacts

**Files:**
- Modify: `.gitignore` (repo root; create if absent)

- [ ] **Step 1: Add build outputs to .gitignore**

Append to the repo-root `.gitignore`:
```text
# Desktop build artifacts
/build/
/dist/
/.build-venv/
```

- [ ] **Step 2: Confirm they are ignored**

Run:
```bash
cd "$REPO" && git check-ignore -q dist && git check-ignore -q .build-venv && echo "ignored OK"
```
Expected: prints `ignored OK`.

- [ ] **Step 3: Commit**

```bash
cd "$REPO"
git add .gitignore
git commit -m "chore: ignore desktop build artifacts (build/, dist/, .build-venv/)"
```

---

## Done criteria

- `cd backend && pytest` green (existing suite + `test_static.py`).
- `pytest desktop/tests` green.
- `bash scripts/build-desktop.sh` produces `dist/Atlas.app`.
- Double-clicking `Atlas.app` opens a native window showing Atlas on demo data, no browser/terminal, and closing it exits cleanly.
- No quarantine attribute on the locally built app.

## Follow-on plans (not in scope here)
- **Plan B — In-app configuration:** frozen-mode settings source (`~/Library/Application Support/Atlas/config.json` + Keychain), `/api/settings`, `/api/status`, OAuth connect + `/oauth/callback`, `/api/test-connection`, React Settings/Integrations page, first-run surface, "Try with demo data" toggle.
- **Plan C — Shareable distribution:** `scripts/install.sh` (Path 1 local build → `~/Applications`), in-app setup instructions incl. ServiceNow scoped-app guidance, risk **R5** added to the CLAUDE.md named-risks table.
