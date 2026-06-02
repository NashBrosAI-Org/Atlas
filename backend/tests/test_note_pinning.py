def test_note_pin_target_roundtrip(client):
    r = client.post("/api/notes", json={
        "title": "Decision: go with phased cutover",
        "note_type": "decision",
        "target_table": "engagement",
        "target_id": "eng123",
        "pinned": True,
    })
    assert r.status_code == 201
    note = r.json()
    assert note["target_table"] == "engagement"
    assert note["target_id"] == "eng123"
    assert note["note_type"] == "decision"

    # list and confirm it can be found by its target
    rows = client.get("/api/notes").json()
    pinned = [n for n in rows if n.get("target_id") == "eng123"]
    assert len(pinned) == 1
