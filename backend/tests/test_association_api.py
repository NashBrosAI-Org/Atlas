def test_associations_endpoint_returns_groups(client):
    cid = client.post("/api/clients", json={"name": "Acme", "status": "active"}).json()["sys_id"]
    client.post("/api/emails", json={"subject": "Hi", "from_addr": "j@acme.com", "client": cid})
    client.post("/api/emails", json={"subject": "Orphan", "from_addr": "x@unknown.com"})
    client.post("/api/meetings", json={"title": "QBR", "attendees": "j@acme.com", "client": cid})

    resp = client.get("/api/associations")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"emails", "meetings"}

    by_label = {e["label"]: e for e in data["emails"]}
    assert by_label["Hi"]["client_name"] == "Acme"
    assert by_label["Orphan"]["client"] == ""
    assert data["meetings"][0]["client_name"] == "Acme"


def test_reassign_email_round_trip(client):
    acme = client.post("/api/clients", json={"name": "Acme", "status": "active"}).json()["sys_id"]
    beta = client.post("/api/clients", json={"name": "Beta", "status": "active"}).json()["sys_id"]
    email_id = client.post(
        "/api/emails", json={"subject": "Hi", "from_addr": "j@acme.com", "client": acme}
    ).json()["sys_id"]

    patch = client.patch(f"/api/emails/{email_id}", json={"client": beta})
    assert patch.status_code == 200

    data = client.get("/api/associations").json()
    row = next(e for e in data["emails"] if e["sys_id"] == email_id)
    assert row["client"] == beta
    assert row["client_name"] == "Beta"
