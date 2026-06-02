def test_all_entity_routes_exist(client):
    for name in ["contacts", "engagements", "themes", "meetings", "transcripts", "notes"]:
        # POST minimal valid bodies
        body = {"name": "x", "client": "c1"} if name in ("contacts", "engagements", "themes") \
            else {"title": "x", "client": "c1"} if name == "meetings" \
            else {"full_text": "x", "client": "c1"} if name == "transcripts" \
            else {"title": "x"}  # notes
        r = client.post(f"/api/{name}", json=body)
        assert r.status_code == 201, f"{name} POST failed: {r.status_code} {r.text}"
        assert client.get(f"/api/{name}").status_code == 200
