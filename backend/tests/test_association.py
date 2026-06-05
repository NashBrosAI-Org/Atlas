from app.servicenow import FakeServiceNow
from app.association import list_associations

SCOPE = "x_test"


async def test_list_associations_resolves_client_names_and_unassociated():
    sn = FakeServiceNow()
    acme = await sn.create(f"{SCOPE}_client", {"name": "Acme", "email_domains": "acme.com"})
    cid = acme["sys_id"]

    await sn.create(f"{SCOPE}_email", {"subject": "Hello", "from_addr": "joe@acme.com", "client": cid})
    await sn.create(f"{SCOPE}_email", {"subject": "Orphan", "from_addr": "x@unknown.com"})
    await sn.create(f"{SCOPE}_meeting", {"title": "QBR", "attendees": "joe@acme.com", "client": cid})

    result = await list_associations(sn, SCOPE)

    assert set(result.keys()) == {"emails", "meetings"}
    assert len(result["emails"]) == 2
    assert len(result["meetings"]) == 1

    by_label = {e["label"]: e for e in result["emails"]}
    assert by_label["Hello"]["client"] == cid
    assert by_label["Hello"]["client_name"] == "Acme"
    assert by_label["Hello"]["who"] == "joe@acme.com"
    assert by_label["Hello"]["type"] == "email"

    # unassociated email
    assert by_label["Orphan"]["client"] == ""
    assert by_label["Orphan"]["client_name"] == ""

    meeting = result["meetings"][0]
    assert meeting["type"] == "meeting"
    assert meeting["label"] == "QBR"
    assert meeting["who"] == "joe@acme.com"
    assert meeting["client_name"] == "Acme"


async def test_list_associations_respects_limit():
    sn = FakeServiceNow()
    for i in range(5):
        await sn.create(f"{SCOPE}_email", {"subject": f"e{i}", "from_addr": "a@b.com"})
        await sn.create(f"{SCOPE}_meeting", {"title": f"m{i}", "attendees": "a@b.com"})

    result = await list_associations(sn, SCOPE, limit=2)
    assert len(result["emails"]) == 2
    assert len(result["meetings"]) == 2
