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
