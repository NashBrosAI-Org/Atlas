import pytest
from fastapi.testclient import TestClient
from app.main import app, get_sn
from app.servicenow import FakeServiceNow


@pytest.fixture
def sn() -> FakeServiceNow:
    return FakeServiceNow()


@pytest.fixture
def client(sn):
    app.dependency_overrides[get_sn] = lambda: sn
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
