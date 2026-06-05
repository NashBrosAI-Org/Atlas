import pytest
from app import drafting
from app.ai import FakeAI
from app.config import get_settings
from app.servicenow import FakeServiceNow

SCOPE = get_settings().sn_scope


@pytest.mark.asyncio
async def test_draft_client_followup_builds_prompt_and_returns_text():
    sn = FakeServiceNow()
    cid = (await sn.create(f"{SCOPE}_client", {"name": "Acme", "status": "active"}))["sys_id"]
    await sn.create(f"{SCOPE}_task", {"title": "Send SOW", "client": cid, "status": "open"})

    captured = {}
    def canned(system, prompt):
        captured["prompt"] = prompt
        return "Subject: Checking in\n\nHi Acme, ..."
    out = await drafting.draft_client_followup(sn, FakeAI(canned=canned), SCOPE, cid)
    assert "Acme" in captured["prompt"] and "Send SOW" in captured["prompt"]
    assert out.startswith("Subject:")


@pytest.mark.asyncio
async def test_draft_unknown_client_returns_none():
    assert await drafting.draft_client_followup(FakeServiceNow(), FakeAI(), SCOPE, "nope") is None
