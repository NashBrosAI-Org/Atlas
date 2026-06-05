import pytest
from app import m365
from app.graph import FakeGraph
from app.servicenow import FakeServiceNow

SCOPE = "x_atlas_sn"

MSG = {
    "id": "AAMk-123", "subject": "Renewal question",
    "receivedDateTime": "2026-06-04T09:00:00Z",
    "from": {"emailAddress": {"address": "jane@acme.com", "name": "Jane"}},
    "toRecipients": [{"emailAddress": {"address": "me@firm.com"}}],
    "body": {"contentType": "text", "content": "Can we discuss the renewal?"},
    "flag": {"flagStatus": "notFlagged"},
}


def test_normalize_message_maps_to_email_row():
    row = m365.normalize_message(MSG)
    assert row["graph_message_id"] == "AAMk-123"
    assert row["subject"] == "Renewal question"
    assert row["from_addr"] == "jane@acme.com"
    assert row["to_addr"] == "me@firm.com"
    assert row["received_date"] == "2026-06-04T09:00:00Z"
    assert row["body"] == "Can we discuss the renewal?"


def test_match_client_by_sender_domain():
    clients = [
        {"sys_id": "c1", "name": "Acme", "email_domains": "acme.com, acme.io"},
        {"sys_id": "c2", "name": "Globex", "email_domains": "globex.com"},
    ]
    assert m365.match_client("jane@acme.com", clients) == "c1"
    assert m365.match_client("bob@ACME.IO", clients) == "c1"
    assert m365.match_client("x@globex.com", clients) == "c2"
    assert m365.match_client("nope@unknown.com", clients) is None
    assert m365.match_client("", clients) is None


async def _seed_client(sn):
    return (await sn.create(f"{SCOPE}_client",
                            {"name": "Acme", "email_domains": "acme.com"}))["sys_id"]


@pytest.mark.asyncio
async def test_ingest_is_idempotent_and_associates_and_flags():
    sn = FakeServiceNow()
    cid = await _seed_client(sn)
    flagged = {**MSG, "id": "AAMk-999", "subject": "Please action",
               "flag": {"flagStatus": "flagged"}}
    graph = FakeGraph(messages=[MSG, flagged])

    first = await m365.ingest_emails(graph, sn, SCOPE)
    assert first == {"ingested": 2, "skipped": 0, "tasks_created": 1}

    emails = await sn.list(f"{SCOPE}_email")
    assert {e["graph_message_id"] for e in emails} == {"AAMk-123", "AAMk-999"}
    assert all(e["client"] == cid for e in emails)

    tasks = await sn.list(f"{SCOPE}_task")
    assert [t["title"] for t in tasks] == ["Follow up: Please action"]
    assert tasks[0]["client"] == cid and tasks[0]["source"] == "email"

    again = await m365.ingest_emails(graph, sn, SCOPE)
    assert again == {"ingested": 0, "skipped": 2, "tasks_created": 0}
    assert len(await sn.list(f"{SCOPE}_email")) == 2
