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
