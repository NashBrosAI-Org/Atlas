import os

# Must run before `app.config` is imported (below, via app.main): disable the
# dev machine's backend/.env so the suite sees code defaults, not the live
# instance config. (CI has no .env, so this is a no-op there.)
os.environ.setdefault("ATLAS_ENV_FILE", "")

import pytest
from fastapi.testclient import TestClient

import app.user_config as uc
from app.main import app
from app.main_deps import get_sn
from app.servicenow import FakeServiceNow


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    """Every test gets a clean per-user state: an empty config.json overlay and no
    real Keychain — so local runs don't depend on the dev machine's saved settings
    or stored password. Tests that need either can re-set them via monkeypatch."""
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(uc.keyring, "get_password", lambda *a, **k: None)


@pytest.fixture
def sn() -> FakeServiceNow:
    return FakeServiceNow()


@pytest.fixture
def client(sn):
    app.dependency_overrides[get_sn] = lambda: sn
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
