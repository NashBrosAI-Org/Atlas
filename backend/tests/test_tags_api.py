from fastapi.testclient import TestClient

import app.main_deps as deps
from app.main import app
from app.servicenow import FakeServiceNow


def _client():
    sn = FakeServiceNow()
    app.dependency_overrides[deps.get_sn] = lambda: sn
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_tag_vocabulary_and_record_tagging():
    c = _client()
    cid = c.post("/api/clients", json={"name": "Acme", "status": "active"}).json()["sys_id"]

    # Attach a tag to the client (creates the tag on the fly).
    r = c.post(f"/api/tags/on/client/{cid}", json={"name": "VIP"})
    assert r.status_code == 201
    assert r.json()["target_id"] == cid

    # Vocabulary now lists the tag.
    vocab = c.get("/api/tags").json()
    assert [t["name"] for t in vocab] == ["VIP"]

    # Idempotent: same name doesn't duplicate.
    c.post(f"/api/tags/on/client/{cid}", json={"name": "vip"})
    assert len(c.get("/api/tags").json()) == 1

    # The record's tags resolve with names + link ids.
    on = c.get(f"/api/tags/on/client/{cid}").json()
    assert [t["name"] for t in on] == ["VIP"]
    tag_id = on[0]["sys_id"]

    # Detach removes the link.
    d = c.delete(f"/api/tags/on/client/{cid}/{tag_id}")
    assert d.status_code == 200
    assert c.get(f"/api/tags/on/client/{cid}").json() == []
    # Detaching again → 404.
    assert c.delete(f"/api/tags/on/client/{cid}/{tag_id}").status_code == 404
