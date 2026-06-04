import json
from pathlib import Path

import app.user_config as uc


def test_load_overlay_empty_when_no_file(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    assert uc.load_overlay() == {}


def test_save_and_load_config_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    uc.save_config({"sn_instance_url": "https://x.service-now.com", "use_fake": False})
    overlay = uc.load_overlay()
    assert overlay["sn_instance_url"] == "https://x.service-now.com"
    assert overlay["use_fake"] is False
    assert json.loads((tmp_path / "config.json").read_text())["use_fake"] is False


def test_password_roundtrip_via_keychain(monkeypatch):
    store = {}
    monkeypatch.setattr(uc.keyring, "set_password", lambda s, k, v: store.__setitem__((s, k), v))
    monkeypatch.setattr(uc.keyring, "get_password", lambda s, k: store.get((s, k)))
    monkeypatch.setattr(uc.keyring, "delete_password", lambda s, k: store.pop((s, k), None))
    uc.save_password("hunter2")
    assert uc.get_password() == "hunter2"
    uc.clear_password()
    assert uc.get_password() is None


def test_get_password_returns_none_when_no_backend(monkeypatch):
    def _raise(*_a, **_k):
        raise uc.keyring.errors.NoKeyringError("no backend")

    monkeypatch.setattr(uc.keyring, "get_password", _raise)
    assert uc.get_password() is None  # must not crash (headless CI has no keyring)
