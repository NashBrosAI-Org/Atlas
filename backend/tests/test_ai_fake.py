import pytest
from app.ai import FakeAI


@pytest.mark.asyncio
async def test_fakeai_returns_canned_and_captures_calls():
    ai = FakeAI(canned="SUMMARY")
    out = await ai.complete(system="sys", prompt="hello", max_tokens=50)
    assert out == "SUMMARY"
    assert ai.calls[-1] == {"system": "sys", "prompt": "hello", "max_tokens": 50}


@pytest.mark.asyncio
async def test_fakeai_callable_canned_sees_prompt():
    ai = FakeAI(canned=lambda system, prompt: f"echo:{prompt}")
    assert await ai.complete(system="s", prompt="p") == "echo:p"
