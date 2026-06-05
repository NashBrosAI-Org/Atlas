import pytest
from app import prioritization
from app.ai import FakeAI
from app.config import get_settings
from app.servicenow import FakeServiceNow

SCOPE = get_settings().sn_scope


@pytest.mark.asyncio
async def test_suggest_focus_includes_open_tasks_and_excludes_done():
    sn = FakeServiceNow()
    await sn.create(f"{SCOPE}_task", {"title": "Renewal", "priority": "critical", "status": "open"})
    await sn.create(f"{SCOPE}_task", {"title": "Archive", "status": "done"})
    captured = {}
    def canned(system, prompt):
        captured["prompt"] = prompt; captured["system"] = system
        return "- Focus on Renewal first."
    out = await prioritization.suggest_focus(sn, FakeAI(canned=canned), SCOPE)
    assert "Renewal" in captured["prompt"]
    assert "Archive" not in captured["prompt"]           # done excluded (active_now_tasks)
    assert "deterministic" in captured["system"].lower()  # advisory framing
    assert out.startswith("- Focus")


@pytest.mark.asyncio
async def test_suggest_focus_does_not_mutate_tasks():
    sn = FakeServiceNow()
    t = await sn.create(f"{SCOPE}_task", {"title": "X", "priority": "low", "status": "open"})
    await prioritization.suggest_focus(sn, FakeAI(canned="..."), SCOPE)
    after = await sn.get(f"{SCOPE}_task", t["sys_id"])
    assert after["priority"] == "low" and after["status"] == "open"   # unchanged
