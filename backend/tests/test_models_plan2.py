from app.models import Contact, Engagement, Theme, Meeting, Transcript, Note

def test_contact_defaults():
    c = Contact(name="Jane Doe", client="c1")
    assert c.sentiment == "neutral"
    assert c.reports_to is None

def test_engagement_defaults():
    e = Engagement(name="Acme Migration", client="c1")
    assert e.status == "on_track"

def test_theme_defaults():
    t = Theme(name="Renewals", client="c1")
    assert t.status == "open"

def test_meeting_defaults():
    m = Meeting(title="Acme QBR", client="c1")
    assert m.type == "teams"

def test_transcript_minimal():
    tr = Transcript(client="c1", full_text="hello world")
    assert tr.source == "manual"

def test_note_defaults_and_target():
    n = Note(title="Risk: timeline", note_type="risk", target_table="engagement", target_id="e1")
    assert n.pinned is False
    assert n.note_type == "risk"
    assert n.target_id == "e1"
