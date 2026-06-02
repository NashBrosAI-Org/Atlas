def test_create_and_list_clients(client):
    r = client.post("/api/clients", json={"name": "Acme Corp", "short_code": "ACME"})
    assert r.status_code == 201
    created = r.json()
    assert created["sys_id"]
    assert created["status"] == "active"

    r2 = client.get("/api/clients")
    assert r2.status_code == 200
    names = [c["name"] for c in r2.json()]
    assert "Acme Corp" in names
