import pytest
from app import summaries
from app.ai import FakeAI
from app.config import get_settings
from app.servicenow import FakeServiceNow

SCOPE = get_settings().sn_scope


@pytest.mark.asyncio
async def test_summarize_client_builds_prompt_and_returns_text():
    sn = FakeServiceNow()
    cid = (await sn.create(f"{SCOPE}_client", {"name": "Acme", "status": "active"}))["sys_id"]
    await sn.create(f"{SCOPE}_task", {"title": "Renewal", "client": cid, "status": "open", "priority": "high"})

    captured = {}
    def canned(system, prompt):
        captured["system"] = system
        captured["prompt"] = prompt
        return "Acme is mid-renewal; one high-priority task open."
    ai = FakeAI(canned=canned)

    out = await summaries.summarize_client(sn, ai, SCOPE, cid)

    assert "Acme" in captured["prompt"]
    assert "Renewal" in captured["prompt"]
    assert "deterministic" in captured["system"].lower() or "assist" in captured["system"].lower()
    assert out.startswith("Acme is mid-renewal")


@pytest.mark.asyncio
async def test_summarize_client_unknown_returns_none():
    sn = FakeServiceNow()
    assert await summaries.summarize_client(sn, FakeAI(), SCOPE, "nope") is None


@pytest.mark.asyncio
async def test_summarize_transcript_includes_full_text():
    sn = FakeServiceNow()
    tid = (await sn.create(f"{SCOPE}_transcript",
                           {"full_text": "We agreed to ship by Q3.", "source": "manual"}))["sys_id"]
    ai = FakeAI(canned=lambda system, prompt: "Agreed: ship by Q3." if "Q3" in prompt else "?")
    out = await summaries.summarize_transcript(sn, ai, SCOPE, tid)
    assert out == "Agreed: ship by Q3."
    assert await summaries.summarize_transcript(sn, FakeAI(), SCOPE, "nope") is None
