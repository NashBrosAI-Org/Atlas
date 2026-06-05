import pytest
from app import m365
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
