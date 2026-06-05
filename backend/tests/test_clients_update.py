from fastapi.testclient import TestClient
import app.main_deps as deps
from app.main import app
from app.servicenow import FakeServiceNow


def teardown_function():
    app.dependency_overrides.clear()


def test_patch_client_updates_fields():
    sn = FakeServiceNow()
    app.dependency_overrides[deps.get_sn] = lambda: sn
    c = TestClient(app)
    cid = c.post("/api/clients", json={"name": "Acme"}).json()["sys_id"]

    r = c.patch(f"/api/clients/{cid}", json={"email_domains": "acme.com", "email_aliases": "x@gmail.com", "status": "active"})
    assert r.status_code == 200
    assert r.json()["email_domains"] == "acme.com"
    assert r.json()["email_aliases"] == "x@gmail.com"

    got = [x for x in c.get("/api/clients").json() if x["sys_id"] == cid][0]
    assert got["email_aliases"] == "x@gmail.com"
