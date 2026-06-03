import app.user_config as uc
from app.config import get_settings


def test_defaults_when_no_overlay(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(uc, "get_password", lambda: None)
    s = get_settings()
    assert s.use_fake is True  # default


def test_overlay_and_password_applied(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    uc.save_config({
        "use_fake": False,
        "sn_instance_url": "https://nnash.service-now.com",
        "sn_oauth_username": "atlas.sdk",
    })
    monkeypatch.setattr(uc, "get_password", lambda: "secret-pw")
    s = get_settings()
    assert s.use_fake is False
    assert s.sn_instance_url == "https://nnash.service-now.com"
    assert s.sn_oauth_username == "atlas.sdk"
    assert s.sn_oauth_password == "secret-pw"
