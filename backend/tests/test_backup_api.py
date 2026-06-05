from pathlib import Path

from fastapi.testclient import TestClient

import app.user_config as uc
import app.main_deps as deps
from app.main import app
from app.servicenow import FakeServiceNow


def _client(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(uc, "get_password", lambda: None)
    sn = FakeServiceNow()
    app.dependency_overrides[deps.get_sn] = lambda: sn
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_status_before_and_after_export(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    c.post("/api/clients", json={"name": "Acme", "status": "active"})

    before = c.get("/api/backup/status")
    assert before.status_code == 200
    assert before.json()["last_backup"] is None
    assert before.json()["count"] == 0
    assert before.json()["stale"] is True

    exported = c.post("/api/backup/export")
    assert exported.status_code == 200
    body = exported.json()
    assert body["counts"]["client"] == 1
    assert Path(body["path"]).is_file()
    assert Path(body["path"]).parent == tmp_path / "backups"

    after = c.get("/api/backup/status")
    assert after.json()["last_backup"] is not None
    assert after.json()["count"] == 1
    assert after.json()["stale"] is False


def test_restore_endpoint(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    # No backup yet → 404.
    assert c.post("/api/backup/restore").status_code == 404

    c.post("/api/clients", json={"name": "Acme", "status": "active"})
    c.post("/api/backup/export")

    r = c.post("/api/backup/restore")
    assert r.status_code == 200
    body = r.json()
    assert body["created"] + body["updated"] >= 1
    assert body["from"].startswith("atlas-backup-")
