def test_dossier_aggregates_client_relations(client):
    cid = client.post("/api/clients", json={"name": "Acme"}).json()["sys_id"]
    other = client.post("/api/clients", json={"name": "Globex"}).json()["sys_id"]

    client.post("/api/contacts", json={"name": "Jane", "client": cid})
    client.post("/api/contacts", json={"name": "Other", "client": other})
    client.post("/api/engagements", json={"name": "Migration", "client": cid})
    client.post("/api/themes", json={"name": "Renewals", "client": cid})
    client.post("/api/tasks", json={"title": "open one", "client": cid, "status": "open"})
    client.post("/api/tasks", json={"title": "done one", "client": cid, "status": "done"})
    client.post("/api/meetings", json={"title": "QBR", "client": cid})
    client.post("/api/notes", json={"title": "pinned", "target_table": "client", "target_id": cid})
    client.post("/api/notes", json={"title": "elsewhere", "target_table": "client", "target_id": other})
    client.post(f"/api/tags/on/client/{cid}", json={"name": "VIP"})
    client.post(f"/api/tags/on/client/{other}", json={"name": "elsewhere"})
    client.post("/api/key-dates", json={"title": "Renewal", "type": "renewal",
                                        "date": "2026-12-01", "client": cid})
    client.post("/api/key-dates", json={"title": "Other KD", "date": "2026-12-01", "client": other})

    d = client.get(f"/api/clients/{cid}/dossier").json()
    assert d["client"]["name"] == "Acme"
    assert [c["name"] for c in d["contacts"]] == ["Jane"]
    assert [e["name"] for e in d["engagements"]] == ["Migration"]
    assert [t["name"] for t in d["themes"]] == ["Renewals"]
    assert [t["title"] for t in d["open_tasks"]] == ["open one"]   # done excluded
    assert [m["title"] for m in d["meetings"]] == ["QBR"]
    assert [n["title"] for n in d["notes"]] == ["pinned"]          # other client's note excluded
    assert [t["name"] for t in d["tags"]] == ["VIP"]              # other client's tag excluded
    assert [k["title"] for k in d["key_dates"]] == ["Renewal"]    # other client's key date excluded


def test_dossier_unknown_client_404(client):
    assert client.get("/api/clients/nope/dossier").status_code == 404
