"""Backload parsers: .eml/.ics/.vtt → Graph-shaped dicts. Includes a cross-check
that parsed output is consumable by the existing m365 normalization pipeline."""
from app import backload, m365

EML = b"""From: Jane Doe <jane@acme.com>
To: me@firm.com, Bob <bob@firm.com>
Subject: Renewal question
Date: Thu, 04 Jun 2026 09:00:00 +0000
Message-ID: <abc123@acme.com>
Content-Type: text/plain; charset="utf-8"

Can we discuss the renewal?
"""

ICS = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:evt-1@acme.com
SUMMARY:Acme QBR
DTSTART:20260610T150000Z
ATTENDEE;CN=Jane Doe;RSVP=TRUE:mailto:jane@acme.com
LOCATION:https://teams.microsoft.com/l/meetup-join/xyz
END:VEVENT
END:VCALENDAR
"""

VTT = """WEBVTT

1
00:00:00.000 --> 00:00:04.000
<v Jane Doe>Hello everyone.</v>

2
00:00:04.000 --> 00:00:08.000
<v Bob>Let's start with the renewal.</v>
"""


def test_eml_to_message_maps_graph_shape():
    msg = backload.eml_to_message(EML)
    assert msg["id"] == "abc123@acme.com"             # Message-ID → dedup key
    assert msg["subject"] == "Renewal question"
    assert msg["from"]["emailAddress"]["address"] == "jane@acme.com"
    assert [r["emailAddress"]["address"] for r in msg["toRecipients"]] == ["me@firm.com", "bob@firm.com"]
    assert msg["receivedDateTime"].startswith("2026-06-04T09:00:00")
    assert msg["body"]["content"] == "Can we discuss the renewal?"


def test_eml_feeds_existing_normalizer():
    # the parsed dict must be consumable by the live ingestion pipeline
    row = m365.normalize_message(backload.eml_to_message(EML))
    assert row["graph_message_id"] == "abc123@acme.com"
    assert row["from_addr"] == "jane@acme.com"
    assert row["subject"] == "Renewal question"


def test_parse_ics_maps_graph_shape_and_online_flag():
    events = backload.parse_ics(ICS)
    assert len(events) == 1
    e = events[0]
    assert e["id"] == "evt-1@acme.com"
    assert e["subject"] == "Acme QBR"
    assert e["start"]["dateTime"] == "2026-06-10T15:00:00Z"
    assert e["attendees"][0]["emailAddress"]["address"] == "jane@acme.com"
    assert e["isOnlineMeeting"] is True
    # and it normalizes via the existing pipeline
    row = m365.normalize_event(e)
    assert row["graph_event_id"] == "evt-1@acme.com" and row["type"] == "teams"


def test_parse_ics_unfolds_folded_lines():
    # real iCalendar folds mid-content: CRLF + a single leading space, joined seamlessly
    folded = (
        "BEGIN:VEVENT\nUID:u2\nSUMMARY:A very long meeting ti\n tle that wraps\n"
        "DTSTART:20260101\nEND:VEVENT\n"
    )
    e = backload.parse_ics(folded)[0]
    assert e["subject"] == "A very long meeting title that wraps"
    assert e["start"]["dateTime"] == "2026-01-01"   # date-only handled


def test_vtt_to_text_keeps_speakers_drops_timing():
    text = backload.vtt_to_text(VTT)
    assert "Jane Doe: Hello everyone." in text
    assert "Bob: Let's start with the renewal." in text
    assert "-->" not in text and "WEBVTT" not in text
