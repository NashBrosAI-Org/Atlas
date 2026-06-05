import app.user_config as uc
import app.main_deps as deps
from app.servicenow import FakeServiceNow, HttpServiceNow


def test_returns_fake_when_use_fake(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(uc, "get_password", lambda: None)
    deps.reset_sn()
    assert isinstance(deps.get_sn(), FakeServiceNow)


def test_returns_basic_auth_http_when_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    uc.save_config({
        "use_fake": False,
        "sn_instance_url": "https://nnash.service-now.com",
        "sn_oauth_username": "atlas.sdk",
    })
    monkeypatch.setattr(uc, "get_password", lambda: "pw")
    deps.reset_sn()
    client = deps.get_sn()
    assert isinstance(client, HttpServiceNow)


def test_get_graph_returns_fake_when_m365_use_fake(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    import app.main_deps as deps
    from app.graph import FakeGraph
    assert isinstance(deps.get_graph(), FakeGraph)


def test_get_ai_returns_fake_when_ai_use_fake(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    import app.main_deps as deps
    from app.ai import FakeAI
    assert isinstance(deps.get_ai(), FakeAI)


def test_reset_sn_picks_up_new_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(uc, "get_password", lambda: None)
    deps.reset_sn()
    assert isinstance(deps.get_sn(), FakeServiceNow)
    uc.save_config({"use_fake": False, "sn_instance_url": "https://nnash.service-now.com",
                    "sn_oauth_username": "u"})
    monkeypatch.setattr(uc, "get_password", lambda: "pw")
    deps.reset_sn()
    assert isinstance(deps.get_sn(), HttpServiceNow)
