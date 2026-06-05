from fastapi.testclient import TestClient

import app.main_deps as deps
from app.main import app
from app.servicenow import FakeServiceNow


def _client():
    app.dependency_overrides[deps.get_sn] = lambda: FakeServiceNow()
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_link_rejects_javascript_scheme():
    c = _client()
    r = c.post("/api/links", json={"title": "evil", "url": "javascript:alert(1)"})
    assert r.status_code == 422


def test_link_rejects_data_scheme():
    c = _client()
    r = c.post("/api/links", json={"title": "evil", "url": "data:text/html,<script>1</script>"})
    assert r.status_code == 422


def test_link_accepts_http_and_https_and_empty():
    c = _client()
    assert c.post("/api/links", json={"title": "ok", "url": "https://example.com"}).status_code == 201
    assert c.post("/api/links", json={"title": "ok", "url": "http://example.com"}).status_code == 201
    # URL is optional — a titled bookmark with no URL is fine.
    assert c.post("/api/links", json={"title": "no url"}).status_code == 201
