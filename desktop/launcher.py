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

    from app.config import get_settings
    settings = get_settings()
    if settings.use_fake:
        import asyncio
        from app.demo_data import seed_demo, seed_demo_graph
        from app.main_deps import get_graph, get_sn
        asyncio.run(seed_demo(get_sn()))
        try:
            # synthetic mail/calendar so M365 sync demonstrates; never block launch
            # (get_graph() raises if m365_use_fake was turned off independently).
            seed_demo_graph(get_graph())
        except Exception as exc:  # noqa: BLE001
            print(f"Atlas demo-graph seed skipped: {exc}", file=sys.stderr)
    else:
        # On-launch backup so a recent off-instance copy of live data always
        # exists (CLAUDE.md rule #3, risks R2/R3). Never block launch on it.
        import asyncio
        from app import backup
        from app.main_deps import get_sn
        try:
            asyncio.run(backup.autobackup_if_stale(
                get_sn(), settings.sn_scope, settings.backup_max_age_days))
        except Exception as exc:  # noqa: BLE001 — backup must not stop the app
            print(f"Atlas auto-backup skipped: {exc}", file=sys.stderr)

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


def _crash_log_path() -> Path:
    base = os.environ.get("ATLAS_DATA_DIR")
    root = Path(base) if base else Path.home() / "Library" / "Application Support" / "Atlas"
    return root / "atlas-error.log"


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException:
        import traceback

        log = _crash_log_path()
        try:
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(traceback.format_exc())
        except OSError:
            pass
        raise
