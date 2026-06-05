"""Deterministic Now ordering — priority → due_date → commitment. Pure domain
logic with no web/framework dependency, shared by the `/now` endpoint and the
morning briefing so the definition of "what to work on" lives in one place."""
from typing import Optional

_PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def now_sort_key(t: dict):
    rank = _PRIORITY_RANK.get(t.get("priority", "medium"), 2)
    due = t.get("due_date") or "9999-12-31"
    commit = 0 if str(t.get("is_commitment")) in ("True", "true", "1") else 1
    return (rank, due, commit)


def active_now_tasks(tasks: list[dict], limit: Optional[int] = None) -> list[dict]:
    """Open tasks (not done) in Now order, optionally capped at `limit`."""
    rows = sorted((t for t in tasks if t.get("status") != "done"), key=now_sort_key)
    return rows[:limit] if limit is not None else rows
