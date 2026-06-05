"""Microsoft Graph access behind an interface, mirroring the ServiceNow seam.
FakeGraph is an in-memory, synthetic stand-in used on the personal Mac and in
tests (hard rule #1 — no corporate data here). HttpGraph (Phase 4) is the live
client, built and authenticated only on the work Mac after the Entra recon GO."""
from typing import Optional, Protocol


class GraphClient(Protocol):
    async def list_messages(self, since: Optional[str] = None) -> list[dict]: ...
    async def list_events(self, start: str, end: str) -> list[dict]: ...


class FakeGraph:
    """Synthetic Graph data. Message/event dicts mirror the Graph v1.0 shapes so
    normalization code is identical against fake and live."""

    def __init__(self, messages: Optional[list[dict]] = None,
                 events: Optional[list[dict]] = None) -> None:
        self._messages = list(messages or [])
        self._events = list(events or [])

    async def list_messages(self, since: Optional[str] = None) -> list[dict]:
        if since is None:
            return list(self._messages)
        return [m for m in self._messages if m.get("receivedDateTime", "") >= since]

    async def list_events(self, start: str, end: str) -> list[dict]:
        def s(e: dict) -> str:
            return e.get("start", {}).get("dateTime", "")
        return [e for e in self._events if start <= s(e) <= end]
