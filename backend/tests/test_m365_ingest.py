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
