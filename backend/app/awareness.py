"""Awareness aggregation: turn the client's child records into a time-ordered
activity feed and a stale-client radar. Pure logic over the ServiceNowClient
interface — unit-tested against FakeServiceNow with an injected clock."""
from datetime import datetime, timezone
from typing import Optional

from app.servicenow import ServiceNowClient


def _parse_dt(ts: str) -> datetime:
    """Parse fake (ISO Z), ISO-offset, or live-SN (`YYYY-MM-DD HH:MM:SS`, naive)
    timestamps into a timezone-aware UTC datetime."""
    dt = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _canonical(ts: str) -> str:
    """Normalize any supported timestamp string to `YYYY-MM-DDTHH:MM:SSZ` so that
    lexical sorting equals chronological sorting. Unparseable values pass through."""
    if not ts:
        return ""
    try:
        return _parse_dt(ts).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return ts


def event_time(record: dict, domain_field: Optional[str] = None) -> str:
    raw = record[domain_field] if (domain_field and record.get(domain_field)) else record.get("sys_created_on", "")
    return _canonical(raw)


def _ev(type_: str, title: str, when: str, client: str, client_name: str,
        status: Optional[str]) -> dict:
    return {"type": type_, "title": title, "when": when,
            "client": client, "client_name": client_name, "status": status}


async def _collect_events(sn: ServiceNowClient, scope: str) -> list[dict]:
    def t(s: str) -> str:
        return f"{scope}_{s}"

    clients = await sn.list(t("client"))
    name_by_id = {c["sys_id"]: c.get("name", "") for c in clients}
    events: list[dict] = []

    for r in await sn.list(t("task")):
        cid = r.get("client", "")
        events.append(_ev("task", f"Task: {r.get('title', '')}", event_time(r),
                          cid, name_by_id.get(cid, ""), r.get("status")))
    for r in await sn.list(t("meeting")):
        cid = r.get("client", "")
        events.append(_ev("meeting", f"Meeting: {r.get('title', '')}",
                          event_time(r, "datetime"), cid, name_by_id.get(cid, ""), None))
    for r in await sn.list(t("transcript")):
        cid = r.get("client", "")
        events.append(_ev("transcript", "Transcript captured",
                          event_time(r, "captured_date"), cid, name_by_id.get(cid, ""),
                          r.get("source")))
    for r in await sn.list(t("engagement")):
        cid = r.get("client", "")
        events.append(_ev("engagement", f"Engagement: {r.get('name', '')}",
                          event_time(r), cid, name_by_id.get(cid, ""), r.get("status")))
    for r in await sn.list(t("note")):
        if r.get("target_table") == "client":
            cid = r.get("target_id", "")
            events.append(_ev("note", f"Note: {r.get('title', '')}", event_time(r),
                              cid, name_by_id.get(cid, ""), r.get("note_type")))
    return events


async def build_timeline(sn: ServiceNowClient, scope: str, client_id: str) -> Optional[list[dict]]:
    client = await sn.get(f"{scope}_client", client_id)
    if client is None:
        return None
    events = [e for e in await _collect_events(sn, scope) if e["client"] == client_id]
    return sorted(events, key=lambda e: e["when"], reverse=True)


async def recent_activity(sn: ServiceNowClient, scope: str, limit: int = 50) -> list[dict]:
    events = await _collect_events(sn, scope)
    events.sort(key=lambda e: e["when"], reverse=True)
    return events[:limit]


def _days_since(iso: str, now: datetime) -> int:
    if not iso:
        return 10 ** 6
    try:
        return (now - _parse_dt(iso)).days
    except ValueError:
        return 10 ** 6


async def stale_radar(sn: ServiceNowClient, scope: str, cooling_days: int,
                      stale_days: int, now: Optional[datetime] = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    clients = [c for c in await sn.list(f"{scope}_client") if c.get("status") == "active"]

    last_by_client: dict[str, str] = {}
    for e in await _collect_events(sn, scope):
        cid = e["client"]
        if cid and (cid not in last_by_client or e["when"] > last_by_client[cid]):
            last_by_client[cid] = e["when"]

    entries: list[dict] = []
    for c in clients:
        cid = c["sys_id"]
        last = last_by_client.get(cid) or c.get("sys_created_on", "")
        days = _days_since(last, now)
        if days >= stale_days:
            tier = "stale"
        elif days >= cooling_days:
            tier = "cooling"
        else:
            continue
        entries.append({"client": cid, "client_name": c.get("name", ""),
                        "last_activity": last, "days_quiet": days, "tier": tier})
    entries.sort(key=lambda x: x["days_quiet"], reverse=True)
    return entries
