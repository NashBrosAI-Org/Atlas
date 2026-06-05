import pytest
from app import extraction
from app.ai import FakeAI

SIG = "Jane Doe\nVP Engineering, Acme Corp\njane@acme.com\n+1 (555) 123-4567"


@pytest.mark.asyncio
async def test_extract_uses_ai_json_when_valid():
    ai = FakeAI(canned='{"name": "Jane Doe", "role_title": "VP Engineering", "email": "jane@acme.com", "phone": "555-1234"}')
    out = await extraction.extract_contact_fields(ai, SIG)
    assert out == {"name": "Jane Doe", "role_title": "VP Engineering", "email": "jane@acme.com", "phone": "555-1234"}


@pytest.mark.asyncio
async def test_extract_falls_back_to_regex_on_junk():
    ai = FakeAI(canned="[not json]")
    out = await extraction.extract_contact_fields(ai, SIG)
    assert out["email"] == "jane@acme.com"
    assert "555" in out["phone"]
    assert out["name"] == "Jane Doe"
    assert out["role_title"] == ""          # regex can't reliably get title; left blank


@pytest.mark.asyncio
async def test_extract_ai_partial_filled_by_regex():
    ai = FakeAI(canned='{"role_title": "VP Engineering"}')  # AI got only the title
    out = await extraction.extract_contact_fields(ai, SIG)
    assert out["role_title"] == "VP Engineering"   # from AI
    assert out["email"] == "jane@acme.com"          # from regex fallback
