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
