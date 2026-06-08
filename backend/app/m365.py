"""Microsoft 365 ingestion: turn Graph messages into retained Email records,
associate them to a client, and raise tasks from flagged mail. Pure logic over
the GraphClient + ServiceNowClient interfaces — unit-tested against FakeGraph +
FakeServiceNow. Retention of mail content in ServiceNow is the consciously-owned
risk R1/D2; keep the ingest filter narrow."""
from typing import Optional

from app import awareness, dossier
from app.graph import FakeGraph, GraphClient
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
    """Return the sys_id of the client matching the sender — by email domain
    (email_domains) or by an explicit full-address alias (email_aliases). Both are
    comma/space-separated, case-insensitive. None if no match."""
    addr = from_addr.strip().lower()
    if not addr:
        return None
    dom = _domain(addr)
    for c in clients:
        domains = {d.strip().lower() for d in (c.get("email_domains") or "").replace(",", " ").split()}
        aliases = {a.strip().lower() for a in (c.get("email_aliases") or "").replace(",", " ").split()}
        if (dom and dom in domains) or (addr in aliases):
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


async def ingest_payload(sn: ServiceNowClient, scope: str,
                         messages: Optional[list[dict]] = None,
                         events: Optional[list[dict]] = None) -> dict:
    """Run the standard mail/calendar ingestion over Graph payloads supplied by the
    *caller* rather than Atlas pulling from Graph itself. This is the "Claude bridge":
    when an in-app Graph app registration isn't available (risk R3), Claude reads mail
    via an approved M365 connector and POSTs the raw Graph JSON here. It reuses the
    exact same normalize/match/dedup/flagged→task pipeline as the live sync — Claude
    stays a dumb pipe; all logic is server-side and deterministic. Retention into SN
    remains the owned risk R1/D2. FakeGraph is just the in-memory GraphClient that
    serves the supplied payload (the data itself is real)."""
    graph = FakeGraph(messages=messages or [], events=events or [])
    result: dict = {}
    if messages:
        result["mail"] = await ingest_emails(graph, sn, scope)
    if events:
        # Wide ISO bounds so every supplied event ingests regardless of its date
        # (ingest_events filters by start.dateTime ∈ [start, end]).
        result["calendar"] = await ingest_events(
            graph, sn, scope, "0000-01-01T00:00:00Z", "9999-12-31T23:59:59Z")
    return result
