"""Microsoft 365 ingestion: turn Graph messages into retained Email records,
associate them to a client, and raise tasks from flagged mail. Pure logic over
the GraphClient + ServiceNowClient interfaces — unit-tested against FakeGraph +
FakeServiceNow. Retention of mail content in ServiceNow is the consciously-owned
risk R1/D2; keep the ingest filter narrow."""
from typing import Optional

from app import awareness, dossier
from app.graph import GraphClient
from app.models import Task
from app.servicenow import ServiceNowClient


def _addr(holder: Optional[dict]) -> str:
    return (holder or {}).get("emailAddress", {}).get("address", "")


def normalize_message(msg: dict) -> dict:
    """Map a Graph message to an x_atlas_sn_email row (minus client/sys_id)."""
    recipients = msg.get("toRecipients") or []
    to_addr = ", ".join(_addr(r) for r in recipients if _addr(r))
    body = (msg.get("body") or {}).get("content") or msg.get("bodyPreview", "")
    return {
        "graph_message_id": msg.get("id", ""),
        "subject": msg.get("subject", ""),
        "from_addr": _addr(msg.get("from")),
        "to_addr": to_addr,
        "received_date": msg.get("receivedDateTime", ""),
        "body": body,
    }


def normalize_event(evt: dict) -> dict:
    """Map a Graph calendar event to an x_atlas_sn_meeting row (minus client/sys_id)."""
    attendees = ", ".join(_addr(a) for a in (evt.get("attendees") or []) if _addr(a))
    return {
        "graph_event_id": evt.get("id", ""),
        "title": evt.get("subject", ""),
        "datetime": (evt.get("start") or {}).get("dateTime", ""),
        "attendees": attendees,
        "type": "teams" if evt.get("isOnlineMeeting") else "other",
    }


def _domain(addr: str) -> str:
    return addr.split("@", 1)[1].lower() if "@" in addr else ""


def match_client(from_addr: str, clients: list[dict]) -> Optional[str]:
    """Return the sys_id of the client whose email_domains contains the sender's
    domain, else None. email_domains is a comma/space-separated list."""
    dom = _domain(from_addr)
    if not dom:
        return None
    for c in clients:
        domains = {d.strip().lower() for d in (c.get("email_domains") or "").replace(",", " ").split()}
        if dom in domains:
            return c.get("sys_id")
    return None


def _is_flagged(msg: dict) -> bool:
    return (msg.get("flag") or {}).get("flagStatus") == "flagged"


async def build_meeting_prep(sn: ServiceNowClient, scope: str, meeting_id: str) -> Optional[dict]:
    """Assemble a prep brief for a meeting: the meeting plus a focused slice of its
    client's dossier (open tasks, key dates, notes) and recent activity. Returns
    None if the meeting doesn't exist; client context is empty if it has no client."""
    meeting = await sn.get(f"{scope}_meeting", meeting_id)
    if meeting is None:
        return None
    client_id = meeting.get("client")
    if not client_id:
        return {"meeting": meeting, "client": None, "open_tasks": [],
                "key_dates": [], "notes": [], "recent_activity": []}
    # NB: dossier.build_dossier resolves the scope from config internally (it has no
    # scope arg), while build_timeline takes one — safe as long as callers pass the
    # configured scope (which they do). Revisit if multi-scope is ever introduced.
    doss = await dossier.build_dossier(sn, client_id)
    timeline = await awareness.build_timeline(sn, scope, client_id) or []
    return {
        "meeting": meeting,
        "client": doss["client"],
        "open_tasks": doss["open_tasks"],
        "key_dates": doss["key_dates"],
        "notes": doss["notes"],
        "recent_activity": timeline[:10],
    }


def _match_client_for_attendees(attendees_csv: str, clients: list[dict]) -> Optional[str]:
    for addr in [a.strip() for a in attendees_csv.split(",") if a.strip()]:
        cid = match_client(addr, clients)
        if cid:
            return cid
    return None


async def ingest_events(graph: GraphClient, sn: ServiceNowClient, scope: str,
                        start: str, end: str) -> dict:
    """Pull calendar events in [start, end], retain new ones as Meeting records
    (idempotent on graph_event_id), associating by attendee domain. Returns counts."""
    existing = {m.get("graph_event_id") for m in await sn.list(f"{scope}_meeting")}
    clients = await sn.list(f"{scope}_client")

    ingested = skipped = 0
    for evt in await graph.list_events(start, end):
        row = normalize_event(evt)
        gid = row["graph_event_id"]
        if not gid or gid in existing:
            skipped += 1
            continue
        client_id = _match_client_for_attendees(row["attendees"], clients)
        if client_id:
            row["client"] = client_id
        await sn.create(f"{scope}_meeting", row)
        existing.add(gid)
        ingested += 1
    return {"ingested": ingested, "skipped": skipped}


async def ingest_emails(graph: GraphClient, sn: ServiceNowClient, scope: str,
                        since: Optional[str] = None) -> dict:
    """Pull messages, retain new ones as Email records (idempotent on
    graph_message_id), associate by sender domain, and raise a Task from each
    flagged message. Returns counts."""
    existing = {e.get("graph_message_id") for e in await sn.list(f"{scope}_email")}
    clients = await sn.list(f"{scope}_client")

    ingested = skipped = tasks_created = 0
    for msg in await graph.list_messages(since=since):
        gid = msg.get("id", "")
        if not gid or gid in existing:
            skipped += 1
            continue
        row = normalize_message(msg)
        client_id = match_client(row["from_addr"], clients)
        if client_id:
            row["client"] = client_id
        await sn.create(f"{scope}_email", row)
        existing.add(gid)
        ingested += 1
        if _is_flagged(msg):
            task = Task(title=f"Follow up: {row['subject']}", source="email", client=client_id)
            await sn.create(f"{scope}_task", task.model_dump(exclude_none=True, exclude={"sys_id"}))
            tasks_created += 1
    return {"ingested": ingested, "skipped": skipped, "tasks_created": tasks_created}
