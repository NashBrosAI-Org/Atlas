from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.crud import crud_router
from app.models import Contact
from app.main_deps import get_sn
from app.servicenow import FakeServiceNow


def _app(sn):
    app = FastAPI()
    app.include_router(crud_router("contacts", "contact", Contact))
    app.dependency_overrides[get_sn] = lambda: sn
    return TestClient(app)


def test_create_get_list_patch_roundtrip():
    sn = FakeServiceNow()
    c = _app(sn)

    created = c.post("/api/contacts", json={"name": "Jane", "client": "c1"}).json()
    assert created["sys_id"]
    assert created["sentiment"] == "neutral"

    got = c.get(f"/api/contacts/{created['sys_id']}").json()
    assert got["name"] == "Jane"

    patched = c.patch(f"/api/contacts/{created['sys_id']}", json={"sentiment": "champion"}).json()
    assert patched["sentiment"] == "champion"

    rows = c.get("/api/contacts").json()
    assert len(rows) == 1


def test_list_filters_by_client():
    sn = FakeServiceNow()
    c = _app(sn)
    c.post("/api/contacts", json={"name": "A", "client": "c1"})
    c.post("/api/contacts", json={"name": "B", "client": "c2"})
    rows = c.get("/api/contacts?client=c1").json()
    assert [r["name"] for r in rows] == ["A"]


def test_get_unknown_returns_404():
    sn = FakeServiceNow()
    c = _app(sn)
    assert c.get("/api/contacts/nope").status_code == 404
