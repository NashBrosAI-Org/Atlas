from fastapi.testclient import TestClient

import app.user_config as uc
import app.main_deps as deps
from app.main import app


def _client(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    store = {}
    monkeypatch.setattr(uc.keyring, "set_password", lambda s, k, v: store.__setitem__((s, k), v))
    monkeypatch.setattr(uc.keyring, "get_password", lambda s, k: store.get((s, k)))
    monkeypatch.setattr(uc.keyring, "delete_password", lambda s, k: store.pop((s, k), None))
    deps.reset_sn()
    return TestClient(app)


def test_status_starts_unconfigured_in_demo(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    r = c.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert body["fake"] is True
    assert body["configured"] is False


def test_get_settings_hides_password_but_reports_presence(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    r = c.get("/api/settings")
    assert r.status_code == 200
    body = r.json()
    assert "sn_oauth_password" not in body
    assert "password" not in body
    assert body["password_set"] is False
    assert body["use_fake"] is True


def test_put_settings_persists_nonsecret_and_password(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    r = c.put("/api/settings", json={
        "use_fake": False,
        "sn_instance_url": "https://nnash.service-now.com",
        "sn_oauth_username": "atlas.sdk",
        "sn_scope": "x_atlas_sn",
        "password": "hunter2",
    })
    assert r.status_code == 200
    assert "password" not in r.json()
    assert "sn_oauth_password" not in r.json()
    assert uc.load_overlay()["sn_instance_url"] == "https://nnash.service-now.com"
    assert uc.get_password() == "hunter2"
    got = c.get("/api/settings").json()
    assert got["password_set"] is True
    assert got["use_fake"] is False


def test_put_settings_without_password_keeps_existing(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    c.put("/api/settings", json={"use_fake": False, "sn_instance_url": "https://x",
                                 "sn_oauth_username": "u", "password": "pw1"})
    c.put("/api/settings", json={"use_fake": False, "sn_instance_url": "https://y",
                                 "sn_oauth_username": "u"})  # no password field
    assert uc.get_password() == "pw1"  # unchanged
    assert uc.load_overlay()["sn_instance_url"] == "https://y"


def test_test_connection_ok_in_demo(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    r = c.post("/api/test-connection")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_test_connection_reports_failure(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)

    class _Boom:
        async def list(self, *a, **k):
            raise RuntimeError("connection refused")

    monkeypatch.setattr(deps, "get_sn", lambda: _Boom())
    r = c.post("/api/test-connection")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert "connection refused" in body["error"]


def test_threshold_settings_roundtrip(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    defaults = c.get("/api/settings").json()
    assert defaults["cooling_days"] == 14 and defaults["stale_days"] == 30
    c.put("/api/settings", json={"cooling_days": 7, "stale_days": 21})
    got = c.get("/api/settings").json()
    assert got["cooling_days"] == 7 and got["stale_days"] == 21


def test_put_settings_round_trips_m365_mail_filter(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    assert c.get("/api/settings").json()["m365_mail_filter"] == "inbox"   # default
    r = c.put("/api/settings", json={"m365_mail_filter": "flagged_only"})
    assert r.status_code == 200
    assert c.get("/api/settings").json()["m365_mail_filter"] == "flagged_only"
