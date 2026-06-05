"""AI access behind an interface, mirroring the ServiceNow/Graph seams. FakeAI is
deterministic — used in tests and as the demo default so AI features demonstrate
with no API key (rule #6: additive, never required). AnthropicAI (a later phase)
is the live client. The deterministic core never calls this; only /api/ai/* does."""
from typing import Callable, Protocol, Union


class AIClient(Protocol):
    async def complete(self, system: str, prompt: str, *, max_tokens: int = 1024) -> str: ...


class FakeAI:
    """Deterministic stand-in. `canned` is either a fixed string or a
    (system, prompt) -> str callable so tests can assert on the prompt."""

    def __init__(self, canned: Union[str, Callable[[str, str], str]] = "[demo summary]") -> None:
        self._canned = canned
        self.calls: list[dict] = []

    async def complete(self, system: str, prompt: str, *, max_tokens: int = 1024) -> str:
        self.calls.append({"system": system, "prompt": prompt, "max_tokens": max_tokens})
        if callable(self._canned):
            return self._canned(system, prompt)
        return self._canned
